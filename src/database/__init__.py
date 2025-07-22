"""
Database package for Snowflake connectivity and query execution.
"""

from .snowflake_connector import SnowflakeConnection, db

__all__ = ['SnowflakeConnection', 'db'] 