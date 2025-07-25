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

def export_llm_feedback_wide():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback.db'))
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT run_id, llm_name, llm_output FROM llm_feedback", conn)
    conn.close()

    if df.empty:
        print("No data to export.")
        return

    # Parse llm_output into generated_sql and output
    df[['generated_sql', 'output']] = df.apply(lambda row: pd.Series(parse_llm_output(row['llm_output'])), axis=1)

    # Get all unique LLMs in the order of first appearance
    llm_order = df.drop_duplicates('llm_name')['llm_name'].tolist()

    # Prepare wide format rows
    wide_rows = []
    for run_id, group in df.groupby('run_id'):
        row = {'run_id': run_id}
        for idx, llm in enumerate(llm_order, 1):
            llm_row = group[group['llm_name'] == llm]
            if not llm_row.empty:
                llm_row = llm_row.iloc[0]
                row[f'Model Name {idx}'] = llm_row['llm_name']
                row[f'Query Created by Model {idx}'] = llm_row['generated_sql']
                row[f'Output of Model {idx}'] = llm_row['output']
            else:
                row[f'Model Name {idx}'] = ''
                row[f'Query Created by Model {idx}'] = ''
                row[f'Output of Model {idx}'] = ''
        wide_rows.append(row)
    wide_df = pd.DataFrame(wide_rows)
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../llm_feedback_export_wide.xlsx'))
    wide_df.to_excel(output_path, index=False)
    print(f"Exported wide-format llm_feedback to {output_path}")

if __name__ == "__main__":
    export_llm_feedback_wide() 