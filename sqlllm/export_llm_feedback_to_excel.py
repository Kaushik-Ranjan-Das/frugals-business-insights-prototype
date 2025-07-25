import os
import sqlite3
import pandas as pd

def export_llm_feedback_to_excel():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback.db'))
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM llm_feedback"
    df = pd.read_sql_query(query, conn)
    conn.close()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback_export.xlsx'))
    df.to_excel(output_path, index=False)
    print(f"Exported llm_feedback table to {output_path}")

if __name__ == "__main__":
    export_llm_feedback_to_excel() 