"""
SQL validation and sanitization utilities.
"""
import re
import sqlparse
from .logging import logger

class SQLValidator:
    """Class to validate and sanitize SQL queries."""
    
    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE',
        'EXEC', 'EXECUTE', 'MERGE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK'
    ]
    
    @classmethod
    def is_safe_query(cls, sql: str) -> bool:
        """
        Check if the SQL query is safe (read-only).
        
        Args:
            sql (str): The SQL query to validate
            
        Returns:
            bool: True if safe, False otherwise
        """
        if not sql or not sql.strip():
            return False
        
        # Remove comments first
        sql_clean = cls._remove_comments(sql)
        
        # Parse and clean the SQL
        try:
            parsed = sqlparse.parse(sql_clean.upper())
            if not parsed:
                return False
            
            # Check for dangerous keywords
            sql_upper = sql_clean.upper()
            for keyword in cls.DANGEROUS_KEYWORDS:
                if re.search(r'\b' + keyword + r'\b', sql_upper):
                    logger.warning(f"Dangerous keyword '{keyword}' found in SQL query")
                    return False
            
            # Check if it starts with safe operations
            first_statement = parsed[0]
            if first_statement.tokens:
                first_token = str(first_statement.tokens[0]).strip().upper()
                if first_token not in ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']:
                    logger.warning(f"Query starts with '{first_token}' which is not allowed")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error parsing SQL: {e}")
            return False
    
    @classmethod
    def sanitize_query(cls, sql: str) -> str:
        """
        Sanitize the SQL query by removing comments and formatting.
        
        Args:
            sql (str): The SQL query to sanitize
            
        Returns:
            str: Sanitized SQL query
        """
        try:
            # Remove comments
            cleaned = cls._remove_comments(sql)
            
            # Split by semicolons and keep only the first statement
            statements = cleaned.split(';')
            first_statement = statements[0].strip()
            
            # Simple formatting - remove extra whitespace
            formatted = ' '.join(first_statement.split())
            
            return formatted + ';' if formatted and not formatted.endswith(';') else formatted
        except Exception as e:
            logger.error(f"Error sanitizing SQL: {e}")
            return sql.strip()
    
    @classmethod
    def _remove_comments(cls, sql: str) -> str:
        """Remove SQL comments from query."""
        # Remove line comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        # Remove block comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql.strip()
    
    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """
        Validate a column name.
        
        Args:
            column_name (str): Column name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not column_name or not isinstance(column_name, str):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [';', '--', '/*', '*/', 'drop', 'delete', 'insert', 'update', 'union', 'select']
        column_lower = column_name.lower()
        
        for pattern in dangerous_patterns:
            if pattern in column_lower:
                return False
        
        # Check if it's a valid identifier (letters, numbers, underscore)
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name) is not None
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """
        Validate a table name.
        
        Args:
            table_name (str): Table name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not table_name or not isinstance(table_name, str):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [';', '--', '/*', '*/', 'drop', 'delete', 'insert', 'update']
        table_lower = table_name.lower()
        
        for pattern in dangerous_patterns:
            if pattern in table_lower:
                return False
        
        # Check if it's a valid identifier (letters, numbers, underscore)
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name) is not None