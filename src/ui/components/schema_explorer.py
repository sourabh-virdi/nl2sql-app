"""
Schema explorer component for browsing database structure.
"""
import streamlit as st
from src.database import db

def display_schema_explorer():
    """Display database schema information."""
    if not st.session_state.db_connected:
        st.warning("Please connect to the database first.")
        return
    
    st.header("📊 Schema Explorer")
    
    # Get table information
    with st.spinner("Loading schema information..."):
        tables_df, tables_error = db.get_table_info()
    
    if tables_error:
        st.error(f"Error loading tables: {tables_error}")
        return
    
    if tables_df is not None and not tables_df.empty:
        st.subheader("Available Tables")
        st.dataframe(tables_df, use_container_width=True)
        
        # Table details
        selected_table = st.selectbox(
            "Select a table to explore:",
            options=[""] + tables_df['TABLE_NAME'].tolist()
        )
        
        if selected_table:
            # Show table structure
            cols_df, cols_error = db.get_table_info(selected_table)
            
            if cols_error:
                st.error(f"Error loading table structure: {cols_error}")
            elif cols_df is not None:
                st.subheader(f"Table Structure: {selected_table}")
                st.dataframe(cols_df, use_container_width=True)
            
            # Show sample data
            sample_df, sample_error = db.get_sample_data(selected_table)
            
            if sample_error:
                st.warning(f"Error loading sample data: {sample_error}")
            elif sample_df is not None and not sample_df.empty:
                st.subheader(f"Sample Data: {selected_table}")
                st.dataframe(sample_df, use_container_width=True)
        
        # Show table relationships
        st.subheader("🔗 Table Relationships")
        relationship_analysis = db.analyze_table_relationships()
        
        # Show table categories
        categories = relationship_analysis.get('table_categories', {})
        if categories:
            st.write("**Table Categories:**")
            categorized_tables = {}
            for table, category in categories.items():
                if category not in categorized_tables:
                    categorized_tables[category] = []
                categorized_tables[category].append(table)
            
            for category, tables in categorized_tables.items():
                st.write(f"• **{category.replace('_', ' ').title()}**: {', '.join(tables)}")
        
        # Show relationships
        explicit_rels = relationship_analysis.get('explicit_relationships', [])
        inferred_rels = relationship_analysis.get('inferred_relationships', [])
        
        if explicit_rels or inferred_rels:
            st.write("**Discovered Relationships:**")
            
            if explicit_rels:
                st.write("*Explicit Foreign Keys:*")
                for rel in explicit_rels:
                    st.write(f"• {rel['CHILD_TABLE']}.{rel['CHILD_COLUMN']} → {rel['PARENT_TABLE']}.{rel['PARENT_COLUMN']}")
            
            if inferred_rels:
                st.write("*Inferred Relationships:*")
                for rel in inferred_rels:
                    confidence = rel.get('confidence', 'medium')
                    st.write(f"• {rel['child_table']}.{rel['child_column']} → {rel['parent_table']}.{rel['parent_column']} ({confidence})")
        else:
            st.info("No table relationships detected. You can still query individual tables.")
        
        # Show common join examples
        join_patterns = relationship_analysis.get('common_join_patterns', {})
        if join_patterns:
            st.write("**Common Join Examples:**")
            for pattern_name, pattern_info in list(join_patterns.items())[:3]:  # Show first 3
                st.code(f"-- {pattern_info['description']}\n-- JOIN condition: {pattern_info['join_condition']}")
        
        # Update schema info for SQL generation with enhanced information
        if tables_df is not None:
            # Generate enhanced schema information including relationships
            enhanced_schema_info = db.generate_enhanced_schema_info()
            st.session_state.current_schema_info = enhanced_schema_info
    
    else:
        st.warning("No tables found in the current schema.") 