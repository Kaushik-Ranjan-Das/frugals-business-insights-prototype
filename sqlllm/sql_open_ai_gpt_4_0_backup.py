import streamlit as st
import os
import sqlite3
import openai
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()

# Set OpenAI API key directly
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Set Hugging Face API token and model
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "Snowflake/Arctic-Text2SQL-R1-7B"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Function to get SQL query from OpenAI (new API)
def get_openai_sql_response(question, prompt, model_name):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt[0]},
            {"role": "user", "content": question}
        ],
        max_tokens=256,
        temperature=0
    )
    sql_query = response.choices[0].message.content.strip()
    return sql_query

# Function to get SQL query from Hugging Face Inference API
def get_hf_sql_response(question, prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    input_text = prompt[0] + "\n" + question
    payload = {"inputs": input_text}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
            return result[0]['generated_text'].strip()
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text'].strip()
        elif isinstance(result, str):
            return result.strip()
        else:
            return str(result)
    else:
        return f"Error from Hugging Face API: {response.status_code} {response.text}"

# Function to retrieve query from the database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.commit()
    conn.close()
    return rows, columns

# Define your prompt for the new schema
prompt = [
    """
    You are an expert in converting English questions to SQL queries! The SQL database is named sales_data.db and contains the following tables and columns:

    1. sales_data_table: client_no, report_no, ims_presc_no, ims_presc_spec, ims_presc_zip, plan_id, sls_cat, rx_type, prod_id, src_id, presc_last_nm, presc_first_nm, presc_mid_nm, presc_street_addr, presc_city, presc_st, presc_zip, supp_data, data_dt, bckt_count, bckt1 ... bckt104
    2. Bckt_To_Week: Week Bucket Name, Week Ending Date
    3. Product_Data_Table: prod_id, Product Name
    4. Presc_Territory_Table: ims_presc_no, Territory
    5. Prescriber_Call_Table: Prescriber ID, Call Date

    Consider Prescriber as Customer. Additionally, all the bckt columns need to be considered as sales columns. Each Bckt column indicates sales for a particular week. To understand the week name please refer to the Bckt_To_Week mapping table e.g. bckt1 would mean sales for week ending 8/18/25, bckt2 would mean week ending 8/11/25 etc.

    For example:
    - How many records are in sales_data_table? -> SELECT COUNT(*) FROM sales_data_table;
    - List all product names in Product_Data_Table. -> SELECT [Product Name] FROM Product_Data_Table;
    - Show all prescribers in territory 'North'. -> SELECT * FROM Presc_Territory_Table WHERE Territory = 'North';
    Do not include ``` or the word 'sql' in your output. Only return the SQL query.
    """
]

# Streamlit App - Facelift
st.set_page_config(page_title="Frugal's Business Insights - Prototype", page_icon="🧠", layout="wide")

with st.sidebar:
    st.title("🧠 Frugal's Business Insights - Prototype")
    tab = st.selectbox("Choose LLM backend", ["OpenAI GPT-4.0", "Hugging Face Arctic-Text2SQL-R1-7B"])
    if tab == "OpenAI GPT-4.0":
        st.markdown(
            """
            **Model Used:**
            - OpenAI GPT-4.0
            - Best for natural language to SQL conversion
            """
        )
    else:
        st.markdown(
            """
            **Model Used:**
            - Hugging Face Arctic-Text2SQL-R1-7B
            - Open-source, local or API-based
            """
        )
    st.markdown("---")
    st.info("Enter your question in natural language and get the SQL instantly!", icon="💡")

# Main UI
st.markdown(f"""
    <style>
    .big-title {{font-size: 2.5em; font-weight: bold; color: #4F8BF9;}}
    .subtitle {{font-size: 1.2em; color: #555;}}
    .sql-box {{background: #f6f8fa; border-radius: 8px; padding: 1em;}}
    .model-banner {{
        font-size: 1.5em;
        font-weight: bold;
        color: #fff;
        background: linear-gradient(90deg, #4F8BF9 60%, #1e3c72 100%);
        border-radius: 8px;
        padding: 0.75em 1em;
        margin-bottom: 1em;
        text-align: center;
        box-shadow: 0 2px 8px rgba(79,139,249,0.08);
    }}
    </style>
    <div class="big-title">Frugal's Business Insights - Prototype</div>
    <div class="subtitle">Ask your data questions in plain English. Powered by <b>{tab}</b>.</div>
    <div class="model-banner">Model in use: {tab}</div>
    <br>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    question = st.text_input("Input your question:", key="input", placeholder="e.g. How many unique clients are there?")
    submit = st.button("Generate SQL Query", use_container_width=True)

with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/2721/2721296.png", width=120)
    st.markdown(f"<b>Model in use:</b> <span style='color:#4F8BF9'>{tab}</span>", unsafe_allow_html=True)

# Use absolute path for the database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sales_data.db"))

# --- Session State Logic ---
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'sql_query' not in st.session_state:
    st.session_state['sql_query'] = None
if 'error' not in st.session_state:
    st.session_state['error'] = None

if submit and question:
    if tab == "OpenAI GPT-4.0":
        sql_query = get_openai_sql_response(question, prompt, "gpt-4")
    else:
        sql_query = get_hf_sql_response(question, prompt)
    st.session_state['sql_query'] = sql_query
    st.markdown("<div class='sql-box'><b>Generated SQL Query:</b></div>", unsafe_allow_html=True)
    st.code(sql_query, language="sql")
    try:
        response, columns = read_sql_query(sql_query, DB_PATH)
        df = pd.DataFrame(response, columns=columns)
        st.session_state['df'] = df
        st.session_state['error'] = None
    except Exception as e:
        st.session_state['df'] = None
        st.session_state['error'] = f"Error executing SQL: {e}"

# --- Visualization Section ---
if st.session_state['sql_query']:
    st.markdown("<div class='sql-box'><b>Generated SQL Query:</b></div>", unsafe_allow_html=True)
    st.code(st.session_state['sql_query'], language="sql")

if st.session_state['error']:
    st.error(st.session_state['error'])

elif st.session_state['df'] is not None:
    df = st.session_state['df']
    if not df.empty:
        st.success("Query executed successfully! Results:")
        viz_type = st.selectbox("Choose visualization type:", ["Table", "Line Chart", "Bar Chart", "Area Chart", "Pie Chart"])
        if viz_type == "Table":
            st.dataframe(df)
        else:
            # Only allow selection of columns if not Table
            columns = df.columns.tolist()
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if len(columns) == 0 or len(numeric_columns) == 0:
                st.warning("No suitable columns for charting.")
            else:
                if viz_type == "Pie Chart":
                    label_col = st.selectbox("Select label (category) column:", columns, key="pie_label_col")
                    value_col = st.selectbox("Select value (numeric) column:", numeric_columns, key="pie_value_col")
                    pie_df = df[[label_col, value_col]].dropna()
                    fig, ax = plt.subplots()
                    ax.pie(pie_df[value_col], labels=pie_df[label_col], autopct='%1.1f%%', startangle=90)
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    x_col = st.selectbox("Select X axis column:", columns, key="x_col")
                    y_col = st.selectbox("Select Y axis column:", numeric_columns, key="y_col")
                    chart_df = df[[x_col, y_col]].dropna()
                    if viz_type == "Line Chart":
                        st.line_chart(chart_df.set_index(x_col))
                    elif viz_type == "Bar Chart":
                        st.bar_chart(chart_df.set_index(x_col))
                    elif viz_type == "Area Chart":
                        st.area_chart(chart_df.set_index(x_col))
    else:
        st.info("Query executed, but returned no results.")









