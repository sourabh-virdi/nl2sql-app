"""
Sidebar component for configuration, connection status, and statistics.
"""
import streamlit as st
from src.config import Config, ENV_TEMPLATE
from src.database import db
from src.genai import sql_generator

def check_configuration():
    """Check if the application is properly configured."""
    try:
        Config.validate_config()
        return True, None
    except ValueError as e:
        return False, str(e)

def test_connections():
    """Test database and Bedrock connections."""
    # Test database connection
    db_success, db_error = db.test_connection()
    st.session_state.db_connected = db_success
    
    # Test Bedrock connection
    bedrock_success, bedrock_error = sql_generator.test_connection()
    st.session_state.bedrock_connected = bedrock_success
    
    return db_success, db_error, bedrock_success, bedrock_error

def display_sidebar():
    """Display the sidebar with configuration and status."""
    with st.sidebar:
        st.title("🔍 NL2SQL App")
        
        # Quick status overview (always visible)
        config_valid, config_error = check_configuration()
        col1, col2 = st.columns(2)
        
        with col1:
            if config_valid:
                st.success("✅ Config OK")
                st.caption("Configuration valid")
            else:
                st.error("❌ Config Error")
                st.caption("Check configuration")
        
        with col2:
            if st.session_state.get('db_connected', False) and st.session_state.get('bedrock_connected', False):
                st.success("✅ Connected")
                st.caption("All systems ready")
            elif st.session_state.get('db_connected', False) or st.session_state.get('bedrock_connected', False):
                st.warning("⚠️ Partial")
                st.caption("Some connections active")
            else:
                st.error("❌ Disconnected")
                st.caption("No connections active")
        
        # Configuration details in expander
        with st.expander("⚙️ Configuration", expanded=not config_valid):
            if config_valid:
                st.success("✅ Configuration is valid")
                st.info("All required settings are properly configured.")
            else:
                st.error("❌ Configuration is invalid")
                st.error(config_error)
                
                st.subheader("Configuration Template")
                st.write("Create a `config/config.toml` file with the following structure:")
                st.code(ENV_TEMPLATE, language="toml")
                return False
        
        # Connection status in expander
        with st.expander("🔌 Connection Status", expanded=True):
            # Test connections button
            if st.button("🔄 Test Connections", help="Test database and GenAI connections"):
                with st.spinner("Testing connections..."):
                    db_success, db_error, bedrock_success, bedrock_error = test_connections()
                
                col1, col2 = st.columns(2)
                with col1:
                    if db_success:
                        st.success("✅ Snowflake connected")
                    else:
                        st.error("❌ Snowflake failed")
                        st.error(db_error)
                
                with col2:
                    if bedrock_success:
                        st.success("✅ AWS Bedrock connected")
                    else:
                        st.error("❌ AWS Bedrock failed")
                        st.error(bedrock_error)
            
            st.divider()
            st.write("**Current Status:**")
            
            # Display current connection status
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.get('db_connected', False):
                    st.success("🟢 Database: Connected")
                else:
                    st.error("🔴 Database: Disconnected")
            
            with col2:
                if st.session_state.get('bedrock_connected', False):
                    st.success("🟢 GenAI: Connected")
                else:
                    st.error("🔴 GenAI: Disconnected")
        
        # Database info in expander
        with st.expander("🗄️ Database Information", expanded=False):
            if st.session_state.db_connected:
                st.info(f"**Database:** {Config.SNOWFLAKE_DATABASE()}")
                st.info(f"**Schema:** {Config.SNOWFLAKE_SCHEMA()}")
                st.info(f"**Warehouse:** {Config.SNOWFLAKE_WAREHOUSE()}")
                st.info(f"**User:** {Config.SNOWFLAKE_USER()}")
            else:
                st.warning("Database not connected")
        
        # Query statistics in expander
        with st.expander("📊 Query Statistics", expanded=False):
            stats = st.session_state.query_logger.get_query_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", stats['total_queries'])
                st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
            
            with col2:
                st.metric("Successful", stats['successful_queries'])
                st.metric("Avg Time", f"{stats['avg_execution_time']:.2f}s")
            
            if stats['total_queries'] > 0:
                st.divider()
                st.write("**Recent Activity:**")
                if stats['successful_queries'] > 0:
                    st.success(f"✅ {stats['successful_queries']} successful queries")
                if stats['total_queries'] - stats['successful_queries'] > 0:
                    st.error(f"❌ {stats['total_queries'] - stats['successful_queries']} failed queries")
        
        # Cache management in expander
        with st.expander("🗃️ Cache Management", expanded=False):
            # Get cache statistics
            cache_stats = st.session_state.cache_manager.get_stats()
            
            st.write("**Cache Statistics:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Entries", cache_stats['total_entries'])
                table_info_count = cache_stats['namespaces'].get('table_info', {}).get('count', 0)
                st.metric("Table Info", table_info_count)
                
            with col2:
                genai_count = cache_stats['namespaces'].get('genai_responses', {}).get('count', 0)
                st.metric("GenAI Responses", genai_count)
                schema_count = cache_stats['namespaces'].get('schema_info', {}).get('count', 0)
                st.metric("Schema Analysis", schema_count)
            
            # Cache namespace details
            if cache_stats['total_entries'] > 0:
                st.divider()
                st.write("**Cache Details by Namespace:**")
                for namespace, details in cache_stats['namespaces'].items():
                    count = details.get('count', 0)
                    if count > 0:
                        newest = details.get('newest_entry')
                        oldest = details.get('oldest_entry')
                        st.write(f"• **{namespace.replace('_', ' ').title()}**: {count} entries")
                        if newest and oldest:
                            age = (newest - oldest).total_seconds() / 60
                            st.write(f"  Age range: {age:.1f} minutes")
            
            # Cache controls
            st.divider()
            st.write("**Cache Controls:**")
                    
            if st.button("🗑️ Clear All Cache", help="Clear all cached data", key="clear_all_cache"):
                cleared = st.session_state.cache_manager.clear_all()
                st.success(f"Cleared {cleared} cache entries!")
                st.rerun()
        
        return True 