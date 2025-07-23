#!/usr/bin/env python3
"""
Natural Language to SQL Query App
Main application entry point.

This application allows users to enter queries in natural language
and get results from a Snowflake database using AWS Bedrock for
natural language to SQL conversion.
"""
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.ui import NL2SQLApp
    
    def main():
        """Main application entry point."""
        app = NL2SQLApp()
        app.run()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Please ensure you have:")
    print("1. Installed all dependencies: pip install -r requirements.txt")
    print("2. Created the config/config.toml file with required configuration")
    print("3. Run the setup test: python tests/test_setup_validation.py")
    sys.exit(1)

except Exception as e:
    print(f"❌ Application error: {e}")
    print("\n💡 Check the logs and configuration for more details.")
    sys.exit(1) 