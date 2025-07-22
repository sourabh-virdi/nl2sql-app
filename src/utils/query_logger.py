"""
Query logging and statistics utilities.
"""
from datetime import datetime
from typing import List, Dict, Any
from .logging import logger

class QueryLogger:
    """Class to log queries and their results."""
    
    def __init__(self):
        self.queries = []
    
    def log_query(self, natural_language: str, sql_query: str, 
                  result_count: int = None, error: str = None, 
                  execution_time: float = None):
        """
        Log a query execution.
        
        Args:
            natural_language (str): The original natural language query
            sql_query (str): The generated SQL query
            result_count (int): Number of rows returned
            error (str): Error message if query failed
            execution_time (float): Query execution time in seconds
        """
        success = not error
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'natural_language': natural_language,
            'sql_query': sql_query,
            'result_count': result_count,
            'error': error,
            'execution_time': execution_time,
            'status': 'success' if success else 'error',
            'success': success
        }
        
        self.queries.append(log_entry)
        
        # Log to file
        if error:
            logger.error(f"Query failed: {natural_language} -> {sql_query} | Error: {error}")
        else:
            logger.info(f"Query executed: {natural_language} -> {sql_query} | "
                       f"Results: {result_count} rows in {execution_time:.2f}s")
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent queries."""
        return self.queries[-limit:] if len(self.queries) > limit else self.queries
    
    def clear_history(self):
        """Clear the query history."""
        self.queries.clear()
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get statistics about query executions."""
        if not self.queries:
            return {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'success_rate': 0,
                'avg_execution_time': 0
            }
        
        successful = [q for q in self.queries if q['status'] == 'success']
        failed = [q for q in self.queries if q['status'] == 'error']
        
        avg_time = 0
        if successful:
            times = [q['execution_time'] for q in successful if q['execution_time']]
            avg_time = sum(times) / len(times) if times else 0
        
        return {
            'total_queries': len(self.queries),
            'successful_queries': len(successful),
            'failed_queries': len(failed),
            'success_rate': len(successful) / len(self.queries) * 100,
            'avg_execution_time': avg_time
        } 