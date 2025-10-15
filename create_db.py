import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from transformers import pipeline
import plotly.express as px

st.set_page_config(page_title="Retail Sales BI Assistant", layout="wide")
st.title("Retail Sales Conversational BI Assistant")

# ---------- Login ----------
st.sidebar.header("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_button = st.sidebar.button("Login")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if login_button:
    if username == "admin" and password == "admin123":
        st.session_state.authenticated = True
        st.success("Login successful!")
    else:
        st.warning("Invalid username/password")

if not st.session_state.authenticated:
    st.stop()

# ---------- Load CSV into SQLite ----------
df = pd.read_csv("retail_sales_data.csv")
engine = create_engine("sqlite:///retail_sales_data.db", echo=False)
df.to_sql("retail_sales_data", con=engine, if_exists="replace", index=False)
st.success("Database loaded successfully!")

# ---------- NLP to SQL ----------
st.sidebar.header("AI Settings")
st.sidebar.info("The AI converts your question into SQL")

nl2sql_model = pipeline("text2text-generation", model="mrm8488/t5-base-finetuned-wikiSQL")

st.subheader("Ask a Question")
user_question = st.text_input("Example: Show total sales by product category")

if st.button("Run Query"):
    if user_question:
        prompt = f"translate English to SQL: {user_question}"
        sql_query = nl2sql_model(prompt, max_length=512)[0]['generated_text']
        st.code(sql_query, language="sql")

        try:
            result_df = pd.read_sql(sql_query, engine)
            st.subheader("Query Result")
            st.dataframe(result_df)

            # ---------- Visualization ----------
            if not result_df.empty:
                for col in result_df.select_dtypes(include='number').columns:
                    st.bar_chart(result_df[col])

                if result_df.shape[1] >= 2:
                    st.plotly_chart(px.line(result_df, x=result_df.columns[0], y=result_df.columns[1],
                                             title="Line Chart"))
                    st.plotly_chart(px.pie(result_df,
                                           names=result_df.columns[0],
                                           values=result_df.select_dtypes(include='number').columns[0],
                                           title="Pie Chart"))
        except Exception as e:
            st.error(f"Error executing query: {e}")
