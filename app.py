import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from datetime import datetime

# Optional: Snowflake imports for deployment
try:
    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas
except ImportError:
    pass

# ----------------- Configuration -----------------
st.set_page_config(page_title="Retail Sales BI", layout="wide")

st.sidebar.title("User Profile")
st.sidebar.write("**User:** Sailee Khedekar D12A&67")
st.sidebar.write(f"**Date:** {datetime.today().strftime('%Y-%m-%d')}")
st.sidebar.write("**Role:** BI Analyst")

# ----------------- Load Dataset -----------------
df = pd.read_csv("retail_sales_dataset.csv")  # Your CSV file

# ----------------- Database Setup -----------------
use_snowflake = False  # Change to True for Snowflake deployment

if use_snowflake:
    # ----------------- Snowflake Connection -----------------
    conn = snowflake.connector.connect(
        user="sailee12",
        password="Newaccount12",
        account="YOUR_ACCOUNT",
        warehouse="YOUR_WAREHOUSE",
        database="YOUR_DATABASE",
        schema="PUBLIC"
    )
    # Upload DataFrame to Snowflake
    write_pandas(conn, df, 'RETAIL_SALES_DATASET')
    st.success("Data uploaded to Snowflake successfully!")
    engine = None  # For query execution, use Snowflake connector directly
else:
    # ----------------- SQLite Connection -----------------
    import sqlite3
    conn = sqlite3.connect("retail_sales_dataset.db")
    df.to_sql("retail_sales_dataset", con=conn, if_exists="replace", index=False)
    st.success("Data loaded into local SQLite database!")
    engine = create_engine("sqlite:///retail_sales_dataset.db", echo=False)

# ----------------- Sidebar Filters -----------------
st.sidebar.title("Filters")
categories = df['Product Category'].unique().tolist()
genders = df['Gender'].unique().tolist()

filter_category = st.sidebar.multiselect("Select Product Category", options=categories, default=[])
filter_gender = st.sidebar.multiselect("Select Gender", options=genders, default=[])

df_filtered = df.copy()
if filter_category:
    df_filtered = df_filtered[df_filtered['Product Category'].isin(filter_category)]
if filter_gender:
    df_filtered = df_filtered[df_filtered['Gender'].isin(filter_gender)]

# ----------------- Main Dashboard -----------------
st.title("🛒 Retail Sales Conversational BI Dashboard")

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Transactions", df_filtered.shape[0])
kpi2.metric("Total Revenue (₹)", int(df_filtered['Total Amount'].sum()))
kpi3.metric("Average Price per Unit (₹)", round(df_filtered['Price per Unit'].mean(), 2))

# ----------------- Load QA Dataset -----------------
qa_df = pd.read_csv("qa_dataset.csv")  # CSV with 'question' and 'sql' columns
qa_dict = dict(zip(qa_df['question'].str.lower(), qa_df['sql']))

# ----------------- User Query -----------------
user_input = st.text_input("Ask a question (example: show total sales by product category):")

if st.button("Run Query"):
    if user_input.strip() == "":
        st.warning("Please enter a question.")
    else:
        question = user_input.lower()
        sql_query = qa_dict.get(question)
        if sql_query:
            try:
                if use_snowflake:
                    # Snowflake query execution
                    cur = conn.cursor()
                    cur.execute(sql_query)
                    data = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    df_result = pd.DataFrame(data, columns=columns)
                else:
                    # SQLite query execution
                    with engine.connect() as conn_sql:
                        result = conn_sql.execute(text(sql_query))
                        data = result.fetchall()
                        columns = result.keys()
                        df_result = pd.DataFrame(data, columns=columns)

                st.subheader("Query Result")
                st.dataframe(df_result)

                # ----------------- Charts -----------------
                if len(df_result.columns) == 2:
                    fig_bar = px.bar(df_result, x=df_result.columns[0], y=df_result.columns[1],
                                     title=f"{user_input.capitalize()}", text=df_result.columns[1])
                    st.plotly_chart(fig_bar, use_container_width=True)

                    fig_pie = px.pie(df_result, names=df_result.columns[0], values=df_result.columns[1],
                                     title=f"{user_input.capitalize()} Distribution")
                    st.plotly_chart(fig_pie, use_container_width=True)
                elif len(df_result.columns) == 1:
                    fig_line = px.line(df_result, y=df_result.columns[0], title=f"{user_input.capitalize()}")
                    st.plotly_chart(fig_line, use_container_width=True)

            except Exception as e:
                st.error(f"SQL Error: {e}")
        else:
            st.info("Question not found in QA dataset. Try another query.")

# ----------------- Visualizations by Filters -----------------
st.subheader("📊 Visualizations by Filters")
if not df_filtered.empty:
    df_grouped = df_filtered.groupby('Product Category')['Total Amount'].sum().reset_index()
    fig = px.bar(df_grouped, x='Product Category', y='Total Amount',
                 title="Total Sales by Product Category", text='Total Amount')
    st.plotly_chart(fig, use_container_width=True)

    df_gender = df_filtered.groupby('Gender')['Total Amount'].sum().reset_index()
    fig2 = px.pie(df_gender, names='Gender', values='Total Amount',
                  title="Revenue Distribution by Gender")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Please select at least one filter to display data.")

# ----------------- Close Connections -----------------
if not use_snowflake:
    conn.close()
