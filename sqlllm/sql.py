import streamlit as st
import os
import sqlite3
import openai
from dotenv import load_dotenv
load_dotenv()

# Set OpenAI API key directly
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Function to get SQL query from OpenAI (new API)
def get_openai_sql_response(question, prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt[0]},
            {"role": "user", "content": question}
        ],
        max_tokens=256,
        temperature=0
    )
    sql_query = response.choices[0].message.content.strip()
    return sql_query

# Function to retrieve query from the database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# Define your prompt for the new schema
prompt = [
    """
    You are an expert in converting English questions to SQL queries! The SQL database is named sales_data.db and contains the following tables and columns:

    1. sales_data_table: client_no, report_no, ims_presc_no, ims_presc_spec, ims_presc_zip, plan_id, sls_cat, rx_type, prod_id, src_id, presc_last_nm, presc_first_nm, presc_mid_nm, presc_street_addr, presc_city, presc_st, presc_zip, supp_data, data_dt, bckt_count, bckt1 ... bckt104
    2. Bckt_To_Week: Week Bucket Name, Week Ending Date
    3. Product_Data_Table: prod_id, Product Name
    4. Presc_Territory_Table: ims_presc_no, Territory
    5. Prescriber_Call_Table: Prescriber ID, Call Date

    For example:
    - How many records are in sales_data_table? -> SELECT COUNT(*) FROM sales_data_table;
    - List all product names in Product_Data_Table. -> SELECT [Product Name] FROM Product_Data_Table;
    - Show all prescribers in territory 'North'. -> SELECT * FROM Presc_Territory_Table WHERE Territory = 'North';
    Do not include ``` or the word 'sql' in your output. Only return the SQL query.
    """
]

# Streamlit App
st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("OpenAI App To Retrieve SQL Data")

question = st.text_input("Input: ", key="input")
submit = st.button("Ask the question")

# Use absolute path for the database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sales_data.db"))

if submit:
    sql_query = get_openai_sql_response(question, prompt)
    st.subheader("Generated SQL Query:")
    st.code(sql_query, language="sql")
    try:
        response = read_sql_query(sql_query, DB_PATH)
        st.subheader("The Response is")
        for row in response:
            st.write(row)
    except Exception as e:
        st.error(f"Error executing SQL: {e}")









