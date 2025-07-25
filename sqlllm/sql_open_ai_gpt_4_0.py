import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import re
import datetime

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sales_data.db"))

# Define the models to compare (OpenRouter model IDs)
OPENROUTER_MODELS = [
    {"name": "Claude 3 Sonnet", "id": "anthropic/claude-3-sonnet"},
    {"name": "Gemini 1.5 Flash", "id": "google/gemini-flash-1.5"},
    {"name": "GPT-4o", "id": "openai/gpt-4o"},
    {"name": "O1-mini", "id": "openai/o1-mini"},
    {"name": "O4-mini", "id": "openai/o4-mini"},
    {"name": "Qwen 3 (reasoning)", "id": "qwen/qwen3-coder:free"}
]

# Function to get SQL query from OpenRouter for a specific model
def get_openrouter_sql_response(question, prompt, model_id):
    if not OPENROUTER_API_KEY:
        return "Error: OpenRouter API key not configured. Please add OPENROUTER_API_KEY to your .env file."
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    # Models that do NOT support 'system' role
    no_system_role_models = [
        "qwen/qwen-110b-chat",
        # Add more model IDs here if needed
    ]
    if model_id in no_system_role_models:
        # Combine prompt and question as a single user message
        messages = [
            {"role": "user", "content": prompt[0] + "\n" + question}
        ]
    else:
        messages = [
            {"role": "system", "content": prompt[0]},
            {"role": "user", "content": question}
        ]
    data = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            return str(result)
    else:
        return f"Error from OpenRouter API: {response.status_code} {response.text}"

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

st.set_page_config(page_title="Frugal's Business Insights - Prototype", page_icon="🧠", layout="wide")
st.title("🧠 Frugal's Business Insights - Prototype")
st.markdown("---")

if not OPENROUTER_API_KEY:
    st.error("⚠️ OpenRouter API key not configured. Please add OPENROUTER_API_KEY to your .env file.")
    st.stop()

st.markdown("## LLM Comparison Table")
question = st.text_input("Write Query Here:")
submit = st.button("Compare Across LLMs")

if 'llm_results' not in st.session_state:
    st.session_state['llm_results'] = None
if 'llm_feedback' not in st.session_state:
    st.session_state['llm_feedback'] = None

# Generate a new run_id if the query changes
if 'last_query' not in st.session_state:
    st.session_state['last_query'] = ''
if 'run_id' not in st.session_state:
    st.session_state['run_id'] = ''
if 'run_counter' not in st.session_state:
    st.session_state['run_counter'] = 1
if question != st.session_state['last_query'] and question:
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    run_id = f"run_{st.session_state['run_counter']}_Date_{now}"
    st.session_state['run_id'] = run_id
    st.session_state['last_query'] = question
    st.session_state['run_counter'] += 1
run_id = st.session_state['run_id']

if run_id:
    st.info(f"Run ID: {run_id}")

if submit and question:
    results = []
    feedback = []
    for model in OPENROUTER_MODELS:
        sql_query = get_openrouter_sql_response(question, prompt, model["id"])
        sql_output = None
        error = None
        if sql_query and not sql_query.startswith("Error:"):
            try:
                response, columns = read_sql_query(sql_query, DB_PATH)
                df = pd.DataFrame(response, columns=columns)
                sql_output = df.to_markdown(index=False) if not df.empty else "(No results)"
            except Exception as e:
                error = f"Error executing SQL: {e}"
        elif sql_query and sql_query.startswith("Error:"):
            error = sql_query
        results.append({
            "Model": model["name"],
            "Generated SQL": sql_query,
            "SQL Output": sql_output if not error else error
        })
    st.session_state['llm_results'] = results
    st.session_state['llm_feedback'] = [{} for _ in results]

# Always show all LLM sections, even before a query is run
llm_section_count = len(OPENROUTER_MODELS)
if st.session_state['llm_results']:
    results = st.session_state['llm_results']
    feedback = st.session_state['llm_feedback']
else:
    # Prepare blank results for display
    results = [{
        "Model": model["name"],
        "Generated SQL": "",
        "SQL Output": ""
    } for model in OPENROUTER_MODELS]
    feedback = [{} for _ in range(llm_section_count)]

for idx, result in enumerate(results):
    st.markdown(f"### {result['Model']}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Generated SQL:**")
        st.code(result["Generated SQL"] or "(No SQL generated)", language="sql")
    with col2:
        st.markdown("**SQL Output:**")
        output_text = result["SQL Output"] or "(No output)"
        if output_text.startswith("Error"):
            st.text_area("Error Output", output_text, height=200, key=f"error_output_{idx}")
        else:
            st.text_area("SQL Output", output_text, height=200, key=f"sql_output_{idx}")
    # Feedback section for this LLM
    st.markdown("**Was this output successful?**")
    feedback_disabled = not st.session_state['llm_results']
    if f'success_{idx}' not in st.session_state:
        st.session_state[f'success_{idx}'] = "Success"
    success = st.radio(
        f"Success/Failure for {result['Model']}",
        ["Success", "Failure", "Error"],
        key=f"success_{idx}",
        disabled=feedback_disabled
    )
    comments = ""
    if success in ["Failure", "Error"] and not feedback_disabled:
        if f'comments_{idx}' not in st.session_state:
            st.session_state[f'comments_{idx}'] = ""
        comments = st.text_area(f"Comments for {result['Model']}", key=f"comments_{idx}")
    feedback[idx] = {
        "run_id": run_id if st.session_state['llm_results'] else "",
        "user_query": question if st.session_state['llm_results'] else "",
        "llm_name": result["Model"],
        "llm_generated_sql": result["Generated SQL"],
        "llm_output": result["SQL Output"],
        "success": 1 if success == "Success" else (0 if success == "Failure" else -1),
        "comments": comments
    }
    # Save feedback immediately to DB if results exist
    if st.session_state['llm_results']:
        feedback_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../llm_feedback.db"))
        conn = sqlite3.connect(feedback_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO llm_feedback (run_id, user_query, llm_name, llm_output, success, comments)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feedback[idx]["run_id"], feedback[idx]["user_query"], feedback[idx]["llm_name"], f"SQL: {feedback[idx]['llm_generated_sql']}\nOutput: {feedback[idx]['llm_output']}", feedback[idx]["success"], feedback[idx]["comments"])
        )
        conn.commit()
        conn.close()
    if idx < len(results) - 1:
        st.markdown("---")
st.session_state['llm_feedback'] = feedback
# Only show submit button if results exist
if st.session_state['llm_results'] and st.button("Submit Feedback"):
    # Generate PDF filename from query
    safe_query = re.sub(r'[^a-zA-Z0-9]+', '_', question)[:50].strip('_')
    pdf_filename = f"llm_feedback_output_{safe_query}.pdf"
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../{pdf_filename}"))
    # Generate PDF with all results and feedback
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="LLM Query and Feedback Report", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"User Query: {question}")
    pdf.ln(5)
    for entry in feedback:
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, txt=f"LLM: {entry['llm_name']}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, f"Generated SQL:\n{entry['llm_generated_sql']}")
        pdf.multi_cell(0, 8, f"SQL Output:\n{entry['llm_output']}")
        status = "Success" if entry['success'] == 1 else ("Failure" if entry['success'] == 0 else "Error")
        pdf.cell(0, 8, txt=f"Feedback: {status}", ln=True)
        if entry['comments']:
            pdf.multi_cell(0, 8, f"Comments: {entry['comments']}")
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    pdf.output(pdf_path)
    st.success(f"Feedback submitted and saved to database! Run ID: {run_id}")
    st.info(f"PDF created and saved as: {pdf_filename}")
    with open(pdf_path, "rb") as f:
        st.download_button("Download Feedback PDF", f, file_name=pdf_filename, mime="application/pdf")
    # Pull and print all values from llm_feedback for this run_id
    feedback_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../llm_feedback.db"))
    conn = sqlite3.connect(feedback_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, run_id, user_query, llm_name, llm_output, success, comments, timestamp FROM llm_feedback WHERE run_id = ? ORDER BY id DESC", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    st.markdown(f"### Feedback Entries for This Run ID: {run_id}")
    if rows:
        for row in rows:
            st.markdown(f"**ID:** {row[0]}")
            st.markdown(f"**Run ID:** {row[1]}")
            st.markdown(f"**User Query:** {row[2]}")
            st.markdown(f"**LLM Name:** {row[3]}")
            st.markdown("**LLM Output:**")
            st.code(row[4])
            status = "Success" if row[5] == 1 else ("Failure" if row[5] == 0 else "Error")
            st.markdown(f"**Feedback:** {status}")
            if row[6]:
                st.markdown(f"**Comments:** {row[6]}")
            st.markdown(f"**Timestamp:** {row[7]}")
            st.markdown("---")
    else:
        st.info("No feedback entries found for this run.")









