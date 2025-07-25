import sqlite3
import os

## Connect to SQLite
db_name = "sales_data.db"
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sales_data.db"))
connection = sqlite3.connect(db_path)

# Create a cursor object to create tables
cursor = connection.cursor()

# Create sales_data_table
sales_data_table = """
CREATE TABLE IF NOT EXISTS sales_data_table (
    client_no TEXT,
    report_no TEXT,
    presc_no TEXT,
    presc_spec TEXT,
    presc_zip TEXT,
    plan_id TEXT,
    sls_cat TEXT,
    rx_type TEXT,
    prod_id TEXT,
    src_id TEXT,
    presc_last_nm TEXT,
    presc_first_nm TEXT,
    presc_mid_nm TEXT,
    presc_street_addr TEXT,
    presc_city TEXT,
    presc_st TEXT,
    presc_zip TEXT,
    supp_data TEXT,
    data_dt TEXT,
    bckt_count INTEGER,
    -- 104 bucket columns
    bckt1 REAL, bckt2 REAL, bckt3 REAL, bckt4 REAL, bckt5 REAL, bckt6 REAL, bckt7 REAL, bckt8 REAL, bckt9 REAL, bckt10 REAL,
    bckt11 REAL, bckt12 REAL, bckt13 REAL, bckt14 REAL, bckt15 REAL, bckt16 REAL, bckt17 REAL, bckt18 REAL, bckt19 REAL, bckt20 REAL,
    bckt21 REAL, bckt22 REAL, bckt23 REAL, bckt24 REAL, bckt25 REAL, bckt26 REAL, bckt27 REAL, bckt28 REAL, bckt29 REAL, bckt30 REAL,
    bckt31 REAL, bckt32 REAL, bckt33 REAL, bckt34 REAL, bckt35 REAL, bckt36 REAL, bckt37 REAL, bckt38 REAL, bckt39 REAL, bckt40 REAL,
    bckt41 REAL, bckt42 REAL, bckt43 REAL, bckt44 REAL, bckt45 REAL, bckt46 REAL, bckt47 REAL, bckt48 REAL, bckt49 REAL, bckt50 REAL,
    bckt51 REAL, bckt52 REAL, bckt53 REAL, bckt54 REAL, bckt55 REAL, bckt56 REAL, bckt57 REAL, bckt58 REAL, bckt59 REAL, bckt60 REAL,
    bckt61 REAL, bckt62 REAL, bckt63 REAL, bckt64 REAL, bckt65 REAL, bckt66 REAL, bckt67 REAL, bckt68 REAL, bckt69 REAL, bckt70 REAL,
    bckt71 REAL, bckt72 REAL, bckt73 REAL, bckt74 REAL, bckt75 REAL, bckt76 REAL, bckt77 REAL, bckt78 REAL, bckt79 REAL, bckt80 REAL,
    bckt81 REAL, bckt82 REAL, bckt83 REAL, bckt84 REAL, bckt85 REAL, bckt86 REAL, bckt87 REAL, bckt88 REAL, bckt89 REAL, bckt90 REAL,
    bckt91 REAL, bckt92 REAL, bckt93 REAL, bckt94 REAL, bckt95 REAL, bckt96 REAL, bckt97 REAL, bckt98 REAL, bckt99 REAL, bckt100 REAL,
    bckt101 REAL, bckt102 REAL, bckt103 REAL, bckt104 REAL
);
"""
cursor.execute(sales_data_table)

# Create Bckt_To_Week table
bckt_to_week_table = """
CREATE TABLE IF NOT EXISTS Bckt_To_Week (
    [Week Bucket Name] TEXT,
    [Week Ending Date] TEXT
);
"""
cursor.execute(bckt_to_week_table)

# Create Product_Data_Table
product_data_table = """
CREATE TABLE IF NOT EXISTS Product_Data_Table (
    prod_id TEXT,
    [Product Name] TEXT
);
"""
cursor.execute(product_data_table)

# Create Presc_Territory_Table
presc_territory_table = """
CREATE TABLE IF NOT EXISTS Presc_Territory_Table (
    presc_no TEXT,
    Territory TEXT
);
"""
cursor.execute(presc_territory_table)

# Create Prescriber_Call_Table
prescriber_call_table = """
CREATE TABLE IF NOT EXISTS Prescriber_Call_Table (
    [Prescriber ID] TEXT,
    [Call Date] TEXT
);
"""
cursor.execute(prescriber_call_table)

print("Tables created successfully in 'sales_data.db'.")

connection.commit()
connection.close()

# --- LLM Feedback DB and Table ---
feedback_db_name = "llm_feedback.db"
feedback_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../llm_feedback.db"))
feedback_conn = sqlite3.connect(feedback_db_path)
feedback_cursor = feedback_conn.cursor()

llm_feedback_table = """
CREATE TABLE IF NOT EXISTS llm_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    user_query TEXT NOT NULL,
    llm_name TEXT NOT NULL,
    llm_output TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    comments TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
feedback_cursor.execute(llm_feedback_table)
# Add run_id column if it doesn't exist (for upgrades)
try:
    feedback_cursor.execute("ALTER TABLE llm_feedback ADD COLUMN run_id TEXT;")
except sqlite3.OperationalError:
    pass  # Column already exists
feedback_conn.commit()
feedback_conn.close()
