"""
Database module for Snowflake connectivity and query execution.
"""
import snowflake.connector
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
import time
from contextlib import contextmanager
from src.config import Config
from src.utils import logger, format_error_message, cache_manager

class SnowflakeConnection:
    """Class to manage Snowflake database connections and queries."""
    
    def __init__(self):
        """Initialize the Snowflake connection manager."""
        self.connection = None
        self._connection_params = {
            'user': Config.SNOWFLAKE_USER(),
            'password': Config.SNOWFLAKE_PASSWORD(),
            'account': Config.SNOWFLAKE_ACCOUNT(),
            'warehouse': Config.SNOWFLAKE_WAREHOUSE(),
            'database': Config.SNOWFLAKE_DATABASE(),
            'schema': Config.SNOWFLAKE_SCHEMA()
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Snowflake.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.connection:
                self.disconnect()
            
            logger.info("Connecting to Snowflake...")
            self.connection = snowflake.connector.connect(**self._connection_params)
            
            # # Set the warehouse explicitly after connection
            # cursor = self.connection.cursor()
            # try:
            #     warehouse = self._connection_params.get('warehouse')
            #     if warehouse:
            #         cursor.execute(f"USE WAREHOUSE {warehouse}")
            #         logger.info(f"Set warehouse to: {warehouse}")
            # finally:
            #     cursor.close()
                
            logger.info("Successfully connected to Snowflake")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            self.connection = None
            return False
    
    def disconnect(self):
        """Close the Snowflake connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Disconnected from Snowflake")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self.connection = None
    
    def is_connected(self) -> bool:
        """
        Check if connected to Snowflake.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connection:
            return False
        
        try:
            # Test the connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for getting a database cursor.
        
        Yields:
            snowflake.connector.cursor.SnowflakeCursor: Database cursor
        """
        if not self.connection or not self.is_connected():
            if not self.connect():
                raise Exception("Unable to establish database connection")
        
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, sql: str) -> Tuple[Optional[pd.DataFrame], Optional[str], float]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql (str): SQL query to execute
            
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[str], float]: 
                (DataFrame with results, error message if any, execution time)
        """
        start_time = time.time()
        
        try:
            with self.get_cursor() as cursor:
                logger.info(f"Executing query: {sql[:100]}...")
                
                # Execute the query
                cursor.execute(sql)
                
                # Fetch results
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                # Convert to DataFrame
                if rows and columns:
                    df = pd.DataFrame(rows, columns=columns)
                    
                    # Limit rows if necessary
                    if len(df) > Config.MAX_ROWS():
                        logger.warning(f"Query returned {len(df)} rows, limiting to {Config.MAX_ROWS()}")
                        df = df.head(Config.MAX_ROWS())
                else:
                    df = pd.DataFrame()
                
                execution_time = time.time() - start_time
                logger.info(f"Query executed successfully in {execution_time:.2f}s, returned {len(df)} rows")
                
                return df, None, execution_time
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = format_error_message(e)
            logger.error(f"Query execution failed: {e}")
            return None, error_msg, execution_time
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test the database connection.
        
        Returns:
            Tuple[bool, Optional[str]]: (Success status, error message if any)
        """
        try:
            if not self.connect():
                return False, "Failed to establish connection"
            
            # Test with a simple query
            df, error, _ = self.execute_query("SELECT CURRENT_TIMESTAMP() as test_time")
            
            if error:
                return False, error
            
            if df is not None and not df.empty:
                return True, None
            else:
                return False, "Connection test returned no results"
                
        except Exception as e:
            return False, format_error_message(e)
    
    def _get_cache_key(self, table_name: Optional[str] = None) -> str:
        """Generate cache key for table info."""
        schema = Config.SNOWFLAKE_SCHEMA()
        database = Config.SNOWFLAKE_DATABASE()
        if table_name:
            return f"{database}.{schema}.{table_name.upper()}.columns"
        else:
            return f"{database}.{schema}.tables"
    
    def clear_table_info_cache(self):
        """Clear the table information cache."""
        cache_manager.clear_namespace("table_info")
        logger.info("Table info cache cleared")
    
    def get_table_info(self, table_name: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Get information about tables in the current schema (with caching).
        
        Args:
            table_name (Optional[str]): Specific table name to get info for
            
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[str]]: (Table info DataFrame, error message if any)
        """
        # Generate cache key
        cache_key = self._get_cache_key(table_name)
        
        # Try to get from cache first
        cached_result = cache_manager.get("table_info", cache_key)
        if cached_result is not None:
            return cached_result['data'], cached_result['error']
        
        # Cache miss - query the database
        logger.info(f"Cache miss for table_info:{cache_key}, querying database...")
        
        try:
            if table_name:
                sql = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{Config.SNOWFLAKE_SCHEMA()}' 
                AND TABLE_NAME = '{table_name.upper()}'
                ORDER BY ORDINAL_POSITION
                """
            else:
                # Build exclusion clauses from configuration
                exclusion_patterns = Config.TABLE_EXCLUSION_PATTERNS()
                exclusion_clauses = ""
                for pattern in exclusion_patterns:
                    exclusion_clauses += f"AND TABLE_NAME NOT LIKE '{pattern}' "
                
                sql = f"""
                SELECT 
                    TABLE_NAME,
                    TABLE_TYPE,
                    ROW_COUNT,
                    COMMENT
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{Config.SNOWFLAKE_SCHEMA()}'
                {exclusion_clauses}
                ORDER BY TABLE_NAME
                """
            
            df, error, _ = self.execute_query(sql)
            
            # Store result in cache
            cache_manager.set(
                namespace="table_info", 
                key=cache_key, 
                value={'data': df, 'error': error},
                expiry_minutes=Config.CACHE_EXPIRY_MINUTES()
            )
            
            return df, error
            
        except Exception as e:
            error_msg = format_error_message(e)
            # Store error in cache too (for shorter time)
            cache_manager.set(
                namespace="table_info", 
                key=cache_key, 
                value={'data': None, 'error': error_msg},
                expiry_minutes=5  # Shorter cache time for errors
            )
            return None, error_msg
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Get sample data from a table.
        
        Args:
            table_name (str): Name of the table
            limit (int): Number of sample rows to return
            
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[str]]: (Sample data DataFrame, error message if any)
        """
        try:
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
            df, error, _ = self.execute_query(sql)
            return df, error
            
        except Exception as e:
            return None, format_error_message(e)
    
    def get_table_relationships(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Get foreign key relationships between tables in the current schema.
        
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[str]]: (Relationships DataFrame, error message if any)
        """
        try:
            sql = f"""
            SELECT 
                fk.TABLE_NAME as CHILD_TABLE,
                fk.COLUMN_NAME as CHILD_COLUMN,
                fk.CONSTRAINT_NAME,
                pk.TABLE_NAME as PARENT_TABLE,
                pk.COLUMN_NAME as PARENT_COLUMN
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk 
                ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME 
                AND rc.CONSTRAINT_SCHEMA = fk.CONSTRAINT_SCHEMA
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk 
                ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME 
                AND rc.UNIQUE_CONSTRAINT_SCHEMA = pk.CONSTRAINT_SCHEMA
            WHERE rc.CONSTRAINT_SCHEMA = '{Config.SNOWFLAKE_SCHEMA()}'
            ORDER BY fk.TABLE_NAME, fk.COLUMN_NAME
            """
            
            df, error, _ = self.execute_query(sql)
            return df, error
            
        except Exception as e:
            return None, format_error_message(e)
    
    def analyze_table_relationships(self) -> Dict[str, Any]:
        """
        Analyze and infer table relationships based on column names and foreign keys.
        
        Returns:
            Dictionary containing relationship analysis
        """
        cache_key = "relationship_analysis"
        
        # Try cache first
        cached_result = cache_manager.get("table_relationships", cache_key)
        if cached_result is not None:
            return cached_result
        
        analysis = {
            'explicit_relationships': [],
            'inferred_relationships': [],
            'common_join_patterns': {},
            'table_categories': {}
        }
        
        try:
            # Get explicit foreign key relationships
            fk_df, fk_error = self.get_table_relationships()
            if fk_df is not None and not fk_df.empty:
                analysis['explicit_relationships'] = fk_df.to_dict('records')
            
            # Get all tables and their columns
            tables_df, _ = self.get_table_info()
            if tables_df is None or tables_df.empty:
                return analysis
            
            # Analyze each table for potential relationships
            for _, table_row in tables_df.iterrows():
                table_name = table_row['TABLE_NAME']
                
                # Get columns for this table
                columns_df, _ = self.get_table_info(table_name)
                if columns_df is None or columns_df.empty:
                    continue
                
                # Categorize table based on name patterns
                table_lower = table_name.lower()
                if any(keyword in table_lower for keyword in ['customer', 'client', 'user']):
                    analysis['table_categories'][table_name] = 'customer_data'
                elif any(keyword in table_lower for keyword in ['account', 'acct']):
                    analysis['table_categories'][table_name] = 'account_data'
                elif any(keyword in table_lower for keyword in ['order', 'transaction', 'payment']):
                    analysis['table_categories'][table_name] = 'transactional'
                elif any(keyword in table_lower for keyword in ['product', 'item', 'catalog']):
                    analysis['table_categories'][table_name] = 'product_data'
                elif any(keyword in table_lower for keyword in ['location', 'address', 'geo']):
                    analysis['table_categories'][table_name] = 'location_data'
                else:
                    analysis['table_categories'][table_name] = 'reference_data'
                
                # Look for foreign key patterns in column names
                for _, column_row in columns_df.iterrows():
                    column_name = column_row['COLUMN_NAME']
                    column_lower = column_name.lower()
                    
                    # Look for ID columns that might reference other tables
                    if column_lower.endswith('_id') and column_lower != 'id':
                        referenced_table = column_lower.replace('_id', '').upper()
                        
                        # Check if the referenced table exists
                        if referenced_table in tables_df['TABLE_NAME'].values:
                            analysis['inferred_relationships'].append({
                                'child_table': table_name,
                                'child_column': column_name,
                                'parent_table': referenced_table,
                                'parent_column': 'ID',  # Assuming standard ID column
                                'confidence': 'high',
                                'type': 'inferred_from_naming'
                            })
                        else:
                            # Try common variations
                            for potential_table in tables_df['TABLE_NAME'].values:
                                if referenced_table in potential_table.lower():
                                    analysis['inferred_relationships'].append({
                                        'child_table': table_name,
                                        'child_column': column_name,
                                        'parent_table': potential_table,
                                        'parent_column': 'ID',
                                        'confidence': 'medium',
                                        'type': 'inferred_from_naming'
                                    })
                                    break
            
            # Generate common join patterns
            for rel in analysis['explicit_relationships'] + analysis['inferred_relationships']:
                parent_table = rel['parent_table']
                child_table = rel['child_table']
                
                join_key = f"{parent_table}_{child_table}"
                analysis['common_join_patterns'][join_key] = {
                    'tables': [parent_table, child_table],
                    'join_condition': f"{parent_table}.{rel['parent_column']} = {child_table}.{rel['child_column']}",
                    'description': f"Join {parent_table} with {child_table}"
                }
            
            # Cache the analysis
            cache_manager.set(
                namespace="table_relationships",
                key=cache_key,
                value=analysis,
                expiry_minutes=Config.CACHE_EXPIRY_MINUTES()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing table relationships: {e}")
        
        return analysis
    
    def generate_enhanced_schema_info(self) -> str:
        """
        Generate enhanced schema information including relationships for AI prompts.
        
        Returns:
            Enhanced schema information string
        """
        cache_key = "enhanced_schema_info"
        
        # Try cache first
        cached_result = cache_manager.get("schema_info", cache_key)
        if cached_result is not None:
            return cached_result
        
        schema_info = []
        
        try:
            # Get table relationships
            relationship_analysis = self.analyze_table_relationships()
            
            # Get all tables
            tables_df, _ = self.get_table_info()
            if tables_df is None or tables_df.empty:
                return "No schema information available"
            
            schema_info.append("=== DATABASE SCHEMA INFORMATION ===")
            schema_info.append(f"Database: {Config.SNOWFLAKE_DATABASE()}")
            schema_info.append(f"Schema: {Config.SNOWFLAKE_SCHEMA()}")
            schema_info.append("")
            
            # Group tables by category
            categories = relationship_analysis.get('table_categories', {})
            categorized_tables = {}
            for table, category in categories.items():
                if category not in categorized_tables:
                    categorized_tables[category] = []
                categorized_tables[category].append(table)
            
            # List tables by category
            schema_info.append("=== TABLE CATEGORIES ===")
            for category, tables in categorized_tables.items():
                schema_info.append(f"{category.upper().replace('_', ' ')}: {', '.join(tables)}")
            schema_info.append("")
            
            # Detailed table information
            schema_info.append("=== DETAILED TABLE INFORMATION ===")
            for _, table_row in tables_df.iterrows():
                table_name = table_row['TABLE_NAME']
                row_count = table_row.get('ROW_COUNT', 'Unknown')
                
                schema_info.append(f"TABLE: {table_name}")
                schema_info.append(f"  Row Count: {row_count}")
                schema_info.append(f"  Category: {categories.get(table_name, 'reference_data')}")
                
                # Get columns
                columns_df, _ = self.get_table_info(table_name)
                if columns_df is not None and not columns_df.empty:
                    schema_info.append("  Columns:")
                    for _, col_row in columns_df.iterrows():
                        col_name = col_row['COLUMN_NAME']
                        col_type = col_row['DATA_TYPE']
                        nullable = col_row.get('IS_NULLABLE', 'YES')
                        schema_info.append(f"    - {col_name} ({col_type}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                schema_info.append("")
            
            # Relationship information
            explicit_rels = relationship_analysis.get('explicit_relationships', [])
            inferred_rels = relationship_analysis.get('inferred_relationships', [])
            
            if explicit_rels or inferred_rels:
                schema_info.append("=== TABLE RELATIONSHIPS ===")
                
                if explicit_rels:
                    schema_info.append("EXPLICIT FOREIGN KEYS:")
                    for rel in explicit_rels:
                        schema_info.append(f"  {rel['CHILD_TABLE']}.{rel['CHILD_COLUMN']} -> {rel['PARENT_TABLE']}.{rel['PARENT_COLUMN']}")
                
                if inferred_rels:
                    schema_info.append("INFERRED RELATIONSHIPS:")
                    for rel in inferred_rels:
                        confidence = rel.get('confidence', 'medium')
                        schema_info.append(f"  {rel['child_table']}.{rel['child_column']} -> {rel['parent_table']}.{rel['parent_column']} ({confidence} confidence)")
                
                schema_info.append("")
            
            # Common join patterns
            join_patterns = relationship_analysis.get('common_join_patterns', {})
            if join_patterns:
                schema_info.append("=== COMMON JOIN PATTERNS ===")
                for pattern_name, pattern_info in join_patterns.items():
                    schema_info.append(f"  {pattern_info['description']}: {pattern_info['join_condition']}")
                schema_info.append("")
            
            result = "\n".join(schema_info)
            
            # Cache the result
            cache_manager.set(
                namespace="schema_info",
                key=cache_key,
                value=result,
                expiry_minutes=Config.CACHE_EXPIRY_MINUTES()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating enhanced schema info: {e}")
            return f"Error generating schema information: {e}"

# Global database connection instance
db = SnowflakeConnection() 