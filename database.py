import sqlite3
import os

DB_PATH = "tenders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            department TEXT,
            category TEXT,
            value TEXT,
            deadline TEXT,
            portal TEXT,
            priority TEXT,
            summary TEXT,
            eligibility_status TEXT,
            eligibility_checks TEXT,
            proposal_structure TEXT,
            ai_recommendation TEXT,
            status TEXT DEFAULT 'new',
            raw_text TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS past_bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            department TEXT,
            category TEXT,
            value TEXT,
            outcome TEXT,
            year INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_id INTEGER,
            type TEXT,
            body TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database created successfully!")

def save_tender(tender: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO tenders 
        (title, department, category, value, deadline, portal,
         priority, summary, eligibility_status, eligibility_checks,
         proposal_structure, ai_recommendation, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tender.get('title'),
        tender.get('department'),
        tender.get('category'),
        tender.get('value'),
        tender.get('deadline'),
        tender.get('portal'),
        tender.get('priority'),
        tender.get('summary'),
        tender.get('eligibility_status'),
        str(tender.get('eligibility_checks', [])),
        str(tender.get('proposal_structure', [])),
        tender.get('ai_recommendation'),
        tender.get('raw_text')
    ))
    conn.commit()
    conn.close()

def get_all_tenders(priority=None, status=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM tenders WHERE 1=1"
    params = []
    
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY scraped_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_tender_status(tender_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tenders SET status = ? WHERE id = ?", (status, tender_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()