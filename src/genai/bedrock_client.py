"""
GenAI module for AWS Bedrock integration and natural language to SQL conversion.
"""
import boto3
import json
import hashlib
from typing import Optional, Tuple, Dict, Any
from src.config import Config
from src.utils import logger, SQLValidator, cache_manager

class BedrockSQLGenerator:
    """Class to handle natural language to SQL conversion using AWS Bedrock."""
    
    def __init__(self):
        """Initialize the Bedrock client."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the AWS Bedrock client."""
        try:
            # Prepare credentials
            credentials = {
                'aws_access_key_id': Config.AWS_ACCESS_KEY_ID(),
                'aws_secret_access_key': Config.AWS_SECRET_ACCESS_KEY(),
                'region_name': Config.AWS_REGION()
            }
            
            # Add session token if available (for temporary credentials)
            session_token = Config.AWS_SESSION_TOKEN()
            if session_token:
                credentials['aws_session_token'] = session_token
                logger.info("Using temporary AWS credentials with session token")
            else:
                logger.info("Using permanent AWS credentials")
            
            self.client = boto3.client('bedrock-runtime', **credentials)
            logger.info("AWS Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None
    
    def _create_prompt(self, natural_language: str, schema_info: str = "") -> str:
        """
        Create a prompt for the LLM to generate SQL.
        
        Args:
            natural_language (str): The user's natural language query
            schema_info (str): Database schema information
            
        Returns:
            str: Formatted prompt for the LLM
        """
        base_prompt = f"""
You are an expert SQL analyst. Convert the following natural language query into a valid SQL query for Snowflake.

CRITICAL: Respond with ONLY the SQL query. No explanations, no markdown, no extra text.

RULES:
1. Only SELECT statements (no INSERT/UPDATE/DELETE/DROP)
2. Use Snowflake SQL syntax
3. Start directly with SELECT, WITH, or SHOW
4. End with semicolon
5. Use LIMIT for large result sets when appropriate
6. Use proper JOINs when data spans multiple tables
7. Use table aliases for better readability
8. Include WHERE clauses for filtering
9. Use appropriate aggregate functions when needed

IMPORTANT JOIN GUIDELINES:
- When the query mentions multiple entities (customer AND location, account AND details), look for relationships between tables
- Use INNER JOIN for required relationships
- Use LEFT JOIN when you want all records from the main entity even if related data is missing
- Always use table aliases (c for CUSTOMER, a for ACCOUNT, etc.)
- Join tables based on foreign key relationships shown in the schema

QUERY EXAMPLES:
- "customers in US" → Look for CUSTOMER table joined with location/address tables
- "account details for customer" → Join CUSTOMER and ACCOUNT tables
- "orders with customer names" → Join ORDERS, CUSTOMER tables
- "products by category" → Join PRODUCT with CATEGORY tables

Database Schema Information:
{schema_info}

Current Database: {Config.SNOWFLAKE_DATABASE()}
Current Schema: {Config.SNOWFLAKE_SCHEMA()}

Natural Language Query: {natural_language}

SQL Query:"""
        
        return base_prompt
    
    def _invoke_model(self, prompt: str) -> Optional[str]:
        """
        Invoke the Bedrock model to generate SQL.
        
        Args:
            prompt (str): The prompt to send to the model
            
        Returns:
            Optional[str]: Generated SQL query or None if failed
        """
        if not self.client:
            logger.error("Bedrock client not initialized")
            return None
        
        try:
            # Prepare the request payload
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=Config.BEDROCK_MODEL_ID(),
                body=json.dumps(payload),
                contentType='application/json'
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and response_body['content']:
                sql_query = response_body['content'][0]['text'].strip()
                
                # Clean up the response - remove any markdown formatting
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                
                # Extract just the SQL query from the response
                extracted_sql = self._extract_sql_from_response(sql_query)
                
                logger.info(f"Generated SQL: {sql_query}")
                return extracted_sql
            else:
                logger.error("No content in Bedrock response")
                return None
                
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}")
            return None
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract the SQL query from the AI response text.
        
        Args:
            response (str): Full AI response including explanations
            
        Returns:
            str: Extracted SQL query
        """
        import re
        
        # Remove extra whitespace and normalize
        response = ' '.join(response.split())
        
        # Common SQL statement starters
        sql_keywords = [
            'SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 
            'CREATE', 'ALTER', 'DROP', 'SHOW', 'DESCRIBE', 'EXPLAIN'
        ]
        
        # Try to find SQL statements
        sql_statements = []
        
        # Look for patterns like "SELECT ... ;" or "WITH ... ;"
        for keyword in sql_keywords:
            # Pattern to match SQL statement starting with keyword
            pattern = rf'\b{keyword}\b.*?;'
            matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
            sql_statements.extend(matches)
        
        if sql_statements:
            # Return the first/longest SQL statement found
            sql_query = max(sql_statements, key=len).strip()
            logger.info(f"Extracted SQL: {sql_query}")
            return sql_query
        
        # If no complete SQL found, try to extract lines that look like SQL
        lines = response.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Check if line starts with SQL keywords or contains SQL-like patterns
            if any(line.upper().startswith(keyword) for keyword in sql_keywords):
                sql_lines.append(line)
            elif line and ('FROM' in line.upper() or 'WHERE' in line.upper() or 'ORDER BY' in line.upper()):
                sql_lines.append(line)
        
        if sql_lines:
            extracted = ' '.join(sql_lines)
            # Ensure it ends with semicolon
            if not extracted.rstrip().endswith(';'):
                extracted += ';'
            logger.info(f"Extracted SQL from lines: {extracted}")
            return extracted
        
        # If all else fails, return the response (it might already be clean SQL)
        logger.warning("Could not extract SQL, returning original response")
        return response
    
    def _generate_cache_key(self, natural_language: str, schema_info: str = "") -> str:
        """
        Generate a cache key for the GenAI request.
        
        Args:
            natural_language: The user's natural language query
            schema_info: Database schema information
            
        Returns:
            Cache key string
        """
        # Create a hash from the query and schema info for cache key
        content = f"{natural_language.lower().strip()}|{schema_info}"
        cache_key = hashlib.md5(content.encode()).hexdigest()
        return cache_key
    
    def generate_sql(self, natural_language: str, schema_info: str = "") -> Tuple[Optional[str], Optional[str]]:
        """
        Generate SQL from natural language query.
        
        Args:
            natural_language (str): User's natural language query
            schema_info (str): Database schema information
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (Generated SQL, error message if any)
        """
        if not natural_language or not natural_language.strip():
            return None, "Please provide a valid query"
        
        # Generate cache key
        cache_key = self._generate_cache_key(natural_language, schema_info)
        
        # Try to get from cache first
        cached_result = cache_manager.get("genai_responses", cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for GenAI query: {natural_language[:50]}...")
            return cached_result['sql'], cached_result['error']
        
        logger.info(f"Cache miss for GenAI query: {natural_language[:50]}...")
        
        try:
            # Create the prompt
            prompt = self._create_prompt(natural_language, schema_info)
            
            # Generate SQL using Bedrock
            sql_query = self._invoke_model(prompt)
            
            if not sql_query:
                error_msg = "Failed to generate SQL query. Please try rephrasing your request."
                # Cache the error for a short time
                cache_manager.set(
                    namespace="genai_responses",
                    key=cache_key,
                    value={'sql': None, 'error': error_msg},
                    expiry_minutes=5
                )
                return None, error_msg
            
            # Validate the generated SQL
            if not SQLValidator.is_safe_query(sql_query):
                logger.warning(f"Generated unsafe SQL: {sql_query}")
                error_msg = "Generated query contains unsafe operations. Only read-only queries are allowed."
                # Cache validation errors for longer since they're deterministic
                cache_manager.set(
                    namespace="genai_responses",
                    key=cache_key,
                    value={'sql': None, 'error': error_msg},
                    expiry_minutes=60
                )
                return None, error_msg
            
            # Sanitize the query
            sanitized_sql = SQLValidator.sanitize_query(sql_query)
            
            # Cache successful result
            cache_manager.set(
                namespace="genai_responses",
                key=cache_key,
                value={'sql': sanitized_sql, 'error': None},
                expiry_minutes=Config.CACHE_EXPIRY_MINUTES()
            )
            
            return sanitized_sql, None
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            error_msg = f"Error generating SQL: {str(e)}"
            # Cache errors for a short time
            cache_manager.set(
                namespace="genai_responses",
                key=cache_key,
                value={'sql': None, 'error': error_msg},
                expiry_minutes=5
            )
            return None, error_msg
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test the Bedrock connection.
        
        Returns:
            Tuple[bool, Optional[str]]: (Success status, error message if any)
        """
        try:
            if not self.client:
                return False, "Bedrock client not initialized"
            
            # Test with a simple query
            test_prompt = "Convert this to SQL: show current time"
            result = self._invoke_model(test_prompt)
            
            if result:
                return True, None
            else:
                return False, "Failed to get response from Bedrock"
                
        except Exception as e:
            return False, f"Bedrock connection test failed: {str(e)}"
    
    def get_query_suggestions(self, table_names: list) -> list:
        """
        Generate sample query suggestions based on available tables and relationships.
        
        Args:
            table_names (list): List of available table names
            
        Returns:
            list: List of suggested natural language queries
        """
        if not table_names:
            return [
                "Show me the current date and time",
                "What tables are available in this database?", 
                "Show me a sample of data from any table"
            ]
        
        suggestions = []
        
        # Import here to avoid circular imports
        from src.database import db
        
        # Get relationship analysis for smarter suggestions
        try:
            relationship_analysis = db.analyze_table_relationships()
            categories = relationship_analysis.get('table_categories', {})
            join_patterns = relationship_analysis.get('common_join_patterns', {})
        except:
            categories = {}
            join_patterns = {}
        
        # Single table suggestions
        suggestions.extend([
            f"Show me sample data from {table_names[0]}",
            f"Count the total records in {table_names[0]}",
            f"Show me the top 10 records from {table_names[0]}",
        ])
        
        # Category-based suggestions
        customer_tables = [t for t, cat in categories.items() if cat == 'customer_data']
        account_tables = [t for t, cat in categories.items() if cat == 'account_data']
        location_tables = [t for t, cat in categories.items() if cat == 'location_data']
        
        if customer_tables:
            suggestions.extend([
                f"Show me all customers with their details",
                f"Find customers from a specific location",
                f"Show me the most recent customer records",
                f"Count customers by region or status"
            ])
        
        if account_tables:
            suggestions.extend([
                f"Show me account information with balances",
                f"Find accounts with specific criteria",
                f"Show me account activity or transactions"
            ])
        
        # JOIN-based suggestions when relationships exist
        if join_patterns:
            suggestions.extend([
                "Show me customer details with their account information",
                "Find customers in a specific location with their accounts",
                "Show me account holders with their full profile information",
                "Get customer names along with their account balances",
                "Find all customers from US with their account details"
            ])
        
        # Multi-table analysis suggestions
        if len(table_names) > 1:
            suggestions.extend([
                "Compare record counts across all tables",
                "Show me relationships between different tables",
                "Find matching records across related tables"
            ])
        
        # Business intelligence suggestions
        suggestions.extend([
            "Show me summary statistics for key metrics",
            "Find records from the last 30 days",
            "Show me data grouped by categories or regions",
            "Count records by different dimensions",
            "Show me trends or patterns in the data"
        ])
        
        # Limit to reasonable number and randomize
        import random
        if len(suggestions) > 12:
            suggestions = random.sample(suggestions, 12)
        
        return suggestions

# Global SQL generator instance
sql_generator = BedrockSQLGenerator() 