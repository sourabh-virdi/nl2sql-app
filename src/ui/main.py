"""
Main UI module for the Natural Language to SQL Query App.
"""
import streamlit as st
from src.config import Config
from src.utils import QueryLogger, cache_manager
from .components import (
    display_sidebar, display_query_interface, 
    display_schema_explorer, display_query_history
)

class NL2SQLApp:
    """Main application class for the Natural Language to SQL Query App."""
    
    def __init__(self):
        """Initialize the Streamlit application."""
        # Configure Streamlit page
        st.set_page_config(
            page_title=Config.APP_TITLE(),
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'query_logger' not in st.session_state:
            st.session_state.query_logger = QueryLogger()
        
        if 'cache_manager' not in st.session_state:
            st.session_state.cache_manager = cache_manager
            # Set default expiry from config
            cache_manager.set_default_expiry(Config.CACHE_EXPIRY_MINUTES())
        
        if 'db_connected' not in st.session_state:
            st.session_state.db_connected = False
        
        if 'bedrock_connected' not in st.session_state:
            st.session_state.bedrock_connected = False
        
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        if 'current_schema_info' not in st.session_state:
            st.session_state.current_schema_info = ""
    
    def run(self):
        """Run the main application."""
        # Check if sidebar configuration is valid
        config_valid = display_sidebar()
        
        if not config_valid:
            st.error("Please configure the application properly before proceeding.")
            return
        
        # Main content area
        tab1, tab2, tab3 = st.tabs(["🔍 Query", "📊 Schema", "📝 History"])
        
        with tab1:
            display_query_interface()
        
        with tab2:
            display_schema_explorer()
        
        with tab3:
            display_query_history()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "**Natural Language to SQL Query App** | "
            "Powered by AWS Bedrock & Snowflake | "
            f"Built with Streamlit"
        ) 