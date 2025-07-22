"""
Configuration module for the Natural Language to SQL Query App.
Reads configuration from TOML file instead of environment variables.
"""
import toml
from pathlib import Path
from typing import Any, Dict

class Config:
    """Application configuration class that reads from TOML file."""
    
    _config_data = None
    _config_file_path = None
    
    @classmethod
    def _load_config(cls):
        """Load configuration from TOML file."""
        if cls._config_data is None:
            # Look for config.toml in config directory
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / 'config' / 'config.toml'
            
            if not config_file.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {config_file}\n"
                    f"Please create config.toml in the config/ directory."
                )
            
            try:
                cls._config_data = toml.load(config_file)
                cls._config_file_path = config_file
            except Exception as e:
                raise ValueError(f"Error loading configuration file {config_file}: {e}")
    
    @classmethod
    def _get_nested_value(cls, keys: str, default: Any = None) -> Any:
        """Get a nested value from config using dot notation (e.g., 'aws.bedrock.region')."""
        cls._load_config()
        
        value = cls._config_data
        for key in keys.split('.'):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    # AWS Bedrock Configuration
    @classmethod
    def AWS_ACCESS_KEY_ID(cls) -> str:
        return cls._get_nested_value('aws.bedrock.access_key_id')
    
    @classmethod
    def AWS_SECRET_ACCESS_KEY(cls) -> str:
        return cls._get_nested_value('aws.bedrock.secret_access_key')
    
    @classmethod
    def AWS_REGION(cls) -> str:
        return cls._get_nested_value('aws.bedrock.region', 'us-east-1')
        
    @classmethod
    def AWS_SESSION_TOKEN(cls) -> str:
        return cls._get_nested_value('aws.bedrock.session_token')
            
    @classmethod
    def BEDROCK_MODEL_ID(cls) -> str:
        return cls._get_nested_value('aws.bedrock.model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Snowflake Configuration
    @classmethod
    def SNOWFLAKE_USER(cls) -> str:
        return cls._get_nested_value('snowflake.user')
    
    @classmethod
    def SNOWFLAKE_PASSWORD(cls) -> str:
        return cls._get_nested_value('snowflake.password')
    
    @classmethod
    def SNOWFLAKE_ACCOUNT(cls) -> str:
        return cls._get_nested_value('snowflake.account')
    
    @classmethod
    def SNOWFLAKE_WAREHOUSE(cls) -> str:
        return cls._get_nested_value('snowflake.warehouse')
    
    @classmethod
    def SNOWFLAKE_DATABASE(cls) -> str:
        return cls._get_nested_value('snowflake.database')
    
    @classmethod
    def SNOWFLAKE_SCHEMA(cls) -> str:
        return cls._get_nested_value('snowflake.schema')
    
    @classmethod
    def SNOWFLAKE_CONNECTION_TIMEOUT(cls) -> int:
        return cls._get_nested_value('snowflake.connection_timeout', 60)
    
    @classmethod
    def SNOWFLAKE_LOGIN_TIMEOUT(cls) -> int:
        return cls._get_nested_value('snowflake.login_timeout', 30)
    
    # Application Configuration
    @classmethod
    def APP_TITLE(cls) -> str:
        return cls._get_nested_value('application.title', 'Natural Language to SQL Query App')
    
    @classmethod
    def MAX_ROWS(cls) -> int:
        return cls._get_nested_value('application.max_rows', 1000)
    
    @classmethod
    def LOG_LEVEL(cls) -> str:
        return cls._get_nested_value('application.log_level', 'INFO')
    
    @classmethod
    def QUERY_TIMEOUT(cls) -> int:
        return cls._get_nested_value('application.query_timeout', 300)
    
    @classmethod
    def MAX_QUERY_HISTORY(cls) -> int:
        return cls._get_nested_value('application.max_query_history', 100)
    
    # Security Configuration
    @classmethod
    def ENABLE_QUERY_LOGGING(cls) -> bool:
        return cls._get_nested_value('security.enable_query_logging', True)
    
    @classmethod
    def ENABLE_ERROR_TRACKING(cls) -> bool:
        return cls._get_nested_value('security.enable_error_tracking', True)
    
    @classmethod
    def ENABLE_DEBUG_MODE(cls) -> bool:
        return cls._get_nested_value('security.enable_debug_mode', False)
    
    # UI Configuration
    @classmethod
    def STREAMLIT_SERVER_PORT(cls) -> int:
        return cls._get_nested_value('ui.server_port', 8501)
    
    @classmethod
    def STREAMLIT_SERVER_ADDRESS(cls) -> str:
        return cls._get_nested_value('ui.server_address', 'localhost')
    
    @classmethod
    def UI_THEME(cls) -> str:
        return cls._get_nested_value('ui.theme', 'light')
    
    @classmethod
    def SHOW_QUERY_SUGGESTIONS(cls) -> bool:
        return cls._get_nested_value('ui.show_query_suggestions', True)
    
    @classmethod
    def DEFAULT_CHART_TYPE(cls) -> str:
        return cls._get_nested_value('ui.default_chart_type', 'auto')
    
    @classmethod
    def SHOW_DEBUG_INFO(cls) -> bool:
        return cls._get_nested_value('ui.show_debug_info', False)
    
    # Feature flags
    @classmethod
    def ENABLE_SQL_PREVIEW(cls) -> bool:
        return cls._get_nested_value('features.enable_sql_preview', True)
    
    @classmethod
    def ENABLE_PERFORMANCE_MONITORING(cls) -> bool:
        return cls._get_nested_value('features.enable_performance_monitoring', True)
    
    @classmethod
    def ENABLE_USAGE_ANALYTICS(cls) -> bool:
        return cls._get_nested_value('features.enable_usage_analytics', False)
    
    @classmethod
    def ENABLE_SCHEMA_CACHE(cls) -> bool:
        return cls._get_nested_value('features.enable_schema_cache', True)
    
    @classmethod
    def ENABLE_QUERY_EXPLAIN(cls) -> bool:
        return cls._get_nested_value('features.enable_query_explain', False)
    
    @classmethod
    def CACHE_EXPIRY_MINUTES(cls) -> int:
        return cls._get_nested_value('features.cache_expiry_minutes', 30)
    
    # Database Configuration
    @classmethod
    def TABLE_EXCLUSION_PATTERNS(cls) -> list:
        """Get table name patterns to exclude from schema discovery."""
        default_patterns = ['%__ct%', '%UPD', '%NRT%', '%QSAM%']
        return cls._get_nested_value('database.table_exclusion_patterns', default_patterns)
    
    # Logging Configuration
    @classmethod
    def LOG_FILE_PATH(cls) -> str:
        return cls._get_nested_value('logging.file_path', 'app.log')
    
    @classmethod
    def LOG_ROTATION_SIZE(cls) -> str:
        return cls._get_nested_value('logging.rotation_size', '10MB')
    
    @classmethod
    def LOG_RETENTION_DAYS(cls) -> int:
        return cls._get_nested_value('logging.retention_days', 30)
    
    @classmethod
    def LOG_FORMAT(cls) -> str:
        return cls._get_nested_value('logging.format', 'standard')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present."""
        cls._load_config()
        
        required_configs = [
            ('aws.bedrock.access_key_id', 'AWS_ACCESS_KEY_ID'),
            ('aws.bedrock.secret_access_key', 'AWS_SECRET_ACCESS_KEY'),
            ('snowflake.user', 'SNOWFLAKE_USER'),
            ('snowflake.password', 'SNOWFLAKE_PASSWORD'),
            ('snowflake.account', 'SNOWFLAKE_ACCOUNT'),
            ('snowflake.warehouse', 'SNOWFLAKE_WAREHOUSE'),
            ('snowflake.database', 'SNOWFLAKE_DATABASE'),
            ('snowflake.schema', 'SNOWFLAKE_SCHEMA'),
        ]
        
        missing_configs = []
        for config_path, display_name in required_configs:
            if not cls._get_nested_value(config_path):
                missing_configs.append(display_name)
        
        if missing_configs:
            raise ValueError(
                f"Missing required configuration values in {cls._config_file_path}: {', '.join(missing_configs)}\n"
                f"Please update your config/config.toml file with the required values."
            )
        
        return True
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        cls._load_config()
        return cls._config_data.copy()
    
    @classmethod
    def reload_config(cls):
        """Reload configuration from file."""
        cls._config_data = None
        cls._load_config()

# Configuration template for documentation
TOML_CONFIG_TEMPLATE = """
# Create a config/config.toml file in the config directory with these sections:

[aws.bedrock]
access_key_id = "your_aws_access_key_here"
secret_access_key = "your_aws_secret_key_here"
region = "us-east-1"
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

[snowflake]
user = "your_snowflake_username"
password = "your_snowflake_password"
account = "your_snowflake_account"
warehouse = "your_warehouse_name"
database = "your_database_name"
schema = "your_schema_name"

[database]
# Table name patterns to exclude from schema discovery
# These are LIKE patterns used in SQL WHERE clauses
table_exclusion_patterns = [
    "%__ct%",     # Change tracking tables
    "%UPD",       # Update tables
    "%NRT%",      # Near real-time tables
    "%QSAM%"      # QSAM tables
]

[application]
title = "Natural Language to SQL Query App"
max_rows = 1000
log_level = "INFO"

[security]
enable_query_logging = true
enable_error_tracking = true

[ui]
theme = "light"
show_query_suggestions = true

[features]
enable_sql_preview = true
enable_performance_monitoring = true
cache_expiry_minutes = 30

[logging]
file_path = "app.log"
"""

# For backward compatibility
ENV_TEMPLATE = TOML_CONFIG_TEMPLATE 