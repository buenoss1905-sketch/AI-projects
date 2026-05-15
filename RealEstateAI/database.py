import sqlite3

def init_db():
    conn = sqlite3.connect('realestate_ai.db')
    cursor = conn.cursor()
    
    # 1. Investor/Tenant Profiles Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT, -- Investor / Tenant
            budget REAL,
            region TEXT,
            property_type TEXT,
            risk_level TEXT,
            goals TEXT,
            raw_transcript TEXT,
            ai_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Local Database Initialized Successfully!")

if __name__ == "__main__":
    init_db()