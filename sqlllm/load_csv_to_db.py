import pandas as pd
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '../sales_data.db')

# CSV file paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '../Raw data')
CSV_FILES = {
    'sales_data_table': 'Sales_Data.csv',
    'Bckt_To_Week': 'Bckt_To_Week.csv',
    'Product_Data_Table': 'Product_Data.csv',
    'Presc_Territory_Table': 'Presc_to_Terr.csv',
    'Prescriber_Call_Table': 'Presc_call_date.csv',
}

def load_csv_to_table(conn, table_name, csv_path):
    df = pd.read_csv(csv_path)
    # Overwrite: delete existing data
    conn.execute(f"DELETE FROM {table_name}")
    df.to_sql(table_name, conn, if_exists='append', index=False)
    print(f"Loaded {len(df)} rows into {table_name} from {os.path.basename(csv_path)}.")

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        for table, csv_file in CSV_FILES.items():
            csv_path = os.path.join(DATA_DIR, csv_file)
            if os.path.exists(csv_path):
                load_csv_to_table(conn, table, csv_path)
            else:
                print(f"CSV file not found: {csv_path}")
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 