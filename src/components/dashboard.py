import streamlit as st
import os
import pandas as pd

def render_dashboard():
    st.header("Dashboards")

    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        st.warning(f"Created '{data_dir}' directory. Please add some Excel/CSV files.")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.csv', '.xls'))]

    if not files:
        st.info("No data files found in 'data/' directory. Upload or add files to get started.")
        for f in os.listdir(data_dir): 
            st.info(f)
        return

    selected_file = st.selectbox("Select a file to view:", files)

    if selected_file:
        file_path = os.path.join(data_dir, selected_file)
        try:
            if selected_file.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Fix for PyArrow serialization error with mixed types
            # Convert object columns to string to avoid ArrowInvalid errors
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)
            
            st.dataframe(df)
            
            with st.expander("File Statistics"):
                st.write(df.describe())
                
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
