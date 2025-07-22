"""
GenAI package for AWS Bedrock integration and natural language to SQL conversion.
"""

from .bedrock_client import BedrockSQLGenerator, sql_generator

__all__ = ['BedrockSQLGenerator', 'sql_generator'] 