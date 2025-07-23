"""
Query interface component for natural language input and result display.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from src.database import db
from src.genai import sql_generator
from src.utils import truncate_text

def display_query_interface():
    """Display the main query interface."""
    st.header("💬 Natural Language Query")
    
    if not (st.session_state.db_connected and st.session_state.bedrock_connected):
        st.warning("Please ensure both database and GenAI connections are established.")
        return
    
    # Get query suggestions
    tables_df, _ = db.get_table_info()
    table_names = tables_df['TABLE_NAME'].tolist() if tables_df is not None else []
    suggestions = sql_generator.get_query_suggestions(table_names)
    
    # Initialize query input in session state if not exists
    if 'query_input' not in st.session_state:
        st.session_state.query_input = ""
    
    # Query input section
    user_query = st.text_area(
        "Enter your question in natural language:",
        value=st.session_state.query_input,
        placeholder="e.g., Show me the top 10 customers by revenue this year",
        height=100,
        key="user_query_textarea"
    )
    
    # Update session state when text area changes
    if user_query != st.session_state.query_input:
        st.session_state.query_input = user_query
    
    # Execute query button
    if st.button("🚀 Execute Query", type="primary", disabled=not user_query):
        execute_natural_language_query(user_query)
    
    # Query suggestions below input
    st.subheader("💡 Query Suggestions")
    st.write("Click any suggestion to use it as your query:")
    
    # Display suggestions in a responsive grid
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions[:8]):  # Show up to 8 suggestions
        col_idx = i % 2
        with cols[col_idx]:
            if st.button(
                truncate_text(suggestion, 60), 
                key=f"suggestion_{hash(suggestion)}",
                help=suggestion,
                use_container_width=True
            ):
                # Update the query input in session state and rerun
                st.session_state.query_input = suggestion
                st.rerun()

def execute_natural_language_query(user_query: str):
    """Execute a natural language query."""
    start_time = time.time()
    
    with st.spinner("🤖 Generating SQL..."):
        # Generate SQL
        sql_query, sql_error = sql_generator.generate_sql(
            user_query, 
            st.session_state.current_schema_info
        )
    
    if sql_error:
        st.error(f"SQL Generation Error: {sql_error}")
        st.session_state.query_logger.log_query(
            user_query, "", error=sql_error
        )
        return
    
    # Display generated SQL
    st.subheader("🔧 Generated SQL")
    st.code(sql_query, language="sql")
    
    # Execute SQL
    with st.spinner("📊 Executing query..."):
        result_df, exec_error, exec_time = db.execute_query(sql_query)
    
    total_time = time.time() - start_time
    
    # Log the query
    if exec_error:
        st.session_state.query_logger.log_query(
            user_query, sql_query, error=exec_error, execution_time=total_time
        )
        st.error(exec_error)
        return
    else:
        result_count = len(result_df) if result_df is not None else 0
        st.session_state.query_logger.log_query(
            user_query, sql_query, result_count=result_count, execution_time=total_time
        )
    
    # Display results
    if result_df is not None and not result_df.empty:
        st.subheader("📈 Query Results")
        
        # Results metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows Returned", len(result_df))
        with col2:
            st.metric("Execution Time", f"{exec_time:.2f}s")
        with col3:
            st.metric("Total Time", f"{total_time:.2f}s")
        
        # Display data
        st.dataframe(result_df, use_container_width=True)
        
        # Visualization options
        if len(result_df.columns) >= 2:
            st.subheader("📊 Data Visualization")
            
            col1, col2 = st.columns(2)
            with col1:
                x_column = st.selectbox("X-axis:", result_df.columns)
            with col2:
                y_column = st.selectbox("Y-axis:", [col for col in result_df.columns if col != x_column])
            
            if x_column and y_column:
                # Determine chart type based on data types
                if result_df[y_column].dtype in ['int64', 'float64']:
                    if len(result_df) <= 20:
                        fig = px.bar(result_df, x=x_column, y=y_column)
                    else:
                        fig = px.line(result_df, x=x_column, y=y_column)
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # Download option
        csv = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("Query executed successfully but returned no results.") 