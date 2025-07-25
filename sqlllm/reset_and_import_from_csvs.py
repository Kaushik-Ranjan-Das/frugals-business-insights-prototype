import os
import sqlite3
import pandas as pd

def get_table_name_from_csv(filename):
    # Remove extension and replace spaces with underscores
    return os.path.splitext(filename)[0].replace(' ', '_')

def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sales_data.db'))
    raw_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Raw data'))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Drop all existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for (table_name,) in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()

    # 2. For each CSV, create table and import data
    for filename in os.listdir(raw_data_dir):
        if filename.endswith('.csv'):
            csv_path = os.path.join(raw_data_dir, filename)
            table_name = get_table_name_from_csv(filename)
            df = pd.read_csv(csv_path)
            # Clean column names: replace spaces with underscores
            df.columns = [c.replace(' ', '_') for c in df.columns]
            df.to_sql(table_name, conn, index=False, if_exists='replace')
            print(f"Imported {filename} into table {table_name}")

    conn.close()
    print("All tables reset and data imported from CSVs.")

if __name__ == "__main__":
    main() 