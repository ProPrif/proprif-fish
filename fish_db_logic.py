import sqlite3

conn = sqlite3.connect("fish.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS zuvys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    temperature REAL NOT NULL,
    aggression TEXT NOT NULL,
    size REAL NOT NULL
)
""")

conn.commit()

print("SQLite duomenų bazė ir lentelė 'fish' sėkmingai sukurta.")

conn.close()