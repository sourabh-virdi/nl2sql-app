"""
Query history component for displaying query logs and analytics.
"""
import streamlit as st
import pandas as pd
from src.utils import truncate_text

def display_query_history():
    """Display query history and analytics."""
    st.header("📝 Query History")
    
    recent_queries = st.session_state.query_logger.get_recent_queries(20)
    
    if not recent_queries:
        st.info("No queries executed yet.")
        return
    
    # Convert to DataFrame for display
    history_df = pd.DataFrame(recent_queries)
    
    # Display recent queries
    st.subheader("Recent Queries")
    
    for i, query in enumerate(recent_queries[::-1]):  # Reverse for newest first
        with st.expander(f"Query {len(recent_queries) - i}: {truncate_text(query['natural_language'], 60)}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Natural Language:**")
                st.write(query['natural_language'])
                
                st.write("**Generated SQL:**")
                st.code(query['sql_query'], language="sql")
                
                if query['error']:
                    st.error(f"Error: {query['error']}")
            
            with col2:
                st.write("**Details:**")
                st.write(f"Time: {query['timestamp']}")
                st.write(f"Status: {query['status']}")
                
                if query['result_count'] is not None:
                    st.write(f"Rows: {query['result_count']}")
                
                if query['execution_time'] is not None:
                    st.write(f"Execution: {query['execution_time']:.2f}s") 