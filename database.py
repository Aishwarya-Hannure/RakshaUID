import sqlite3

DB_NAME = "raksha_database.db"

def init_db():
    """Creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified_users (
            aadhaar_number TEXT PRIMARY KEY,
            name TEXT,
            dob TEXT,
            gender TEXT,
            status TEXT,
            confidence REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_aadhaar(aadhaar_number):
    """Checks if Aadhaar exists in DB."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verified_users WHERE aadhaar_number=?", (aadhaar_number,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "aadhaar_number": row[0],
            "name": row[1],
            "dob": row[2],
            "gender": row[3],
            "status": row[4],
            "confidence": row[5]
        }
    return None

def save_verified_user(data):
    """Saves a user ONLY if they are ACCEPTED and not already in DB."""
    if data.get("status") != "ACCEPTED":
        return  # Don't save Fraud/Suspicious

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO verified_users (aadhaar_number, name, dob, gender, status, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['aadhaar_number'], 
            data['name'], 
            data['dob'], 
            data['gender'], 
            "ACCEPTED", 
            data['confidence']
        ))
        conn.commit()
        print(f"Saved {data['name']} to Database.")
    except sqlite3.IntegrityError:
        print("User already exists in Database. Skipping.")
    
    conn.close()

# Initialize the DB immediately when this file is imported
init_db()