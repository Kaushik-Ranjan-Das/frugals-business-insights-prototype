import os
import sqlite3
import pandas as pd
import re

def parse_llm_output(llm_output):
    sql_match = re.search(r'SQL:(.*?)Output:', llm_output, re.DOTALL)
    out_match = re.search(r'Output:(.*)', llm_output, re.DOTALL)
    generated_sql = sql_match.group(1).strip() if sql_match else ''
    output = out_match.group(1).strip() if out_match else llm_output
    return generated_sql, output

def export_llm_feedback_long():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback.db'))
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT run_id, llm_name, llm_output FROM llm_feedback", conn)
    conn.close()

    if df.empty:
        print("No data to export.")
        return

    # Parse llm_output into generated_sql and output
    df[['Query Created by Model', 'Output of Model']] = df.apply(lambda row: pd.Series(parse_llm_output(row['llm_output'])), axis=1)
    df.rename(columns={'llm_name': 'Model Name'}, inplace=True)
    df['off'] = ''  # Add blank 'off' column
    export_df = df[['run_id', 'Model Name', 'Query Created by Model', 'Output of Model', 'off']]
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback_export_long.xlsx'))
    export_df.to_excel(output_path, index=False)
    print(f"Exported long-format llm_feedback to {output_path}")

if __name__ == "__main__":
    export_llm_feedback_long() 