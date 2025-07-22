"""
General helper functions for the Natural Language to SQL Query App.
"""

def format_error_message(error: Exception) -> str:
    """
    Format error messages for user display.
    
    Args:
        error (Exception): The exception to format
        
    Returns:
        str: User-friendly error message
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    if 'connection' in error_str:
        return f"❌ Unable to connect to the database. Please check your connection settings. ({error_type}: {str(error)})"
    elif 'authentication' in error_str or 'login' in error_str:
        return f"❌ Authentication failed. Please check your credentials. ({error_type}: {str(error)})"
    elif 'permission' in error_str or 'access' in error_str:
        return f"❌ Permission denied. You don't have access to this resource. ({error_type}: {str(error)})"
    elif 'timeout' in error_str:
        return f"❌ Query timed out. Try simplifying your request. ({error_type}: {str(error)})"
    elif 'syntax' in error_str:
        return f"❌ SQL syntax error. The generated query has invalid syntax. ({error_type}: {str(error)})"
    else:
        return f"❌ An error occurred: {str(error)} ({error_type})"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text with ellipsis if it's too long.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."