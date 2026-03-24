import sqlite3

conn = sqlite3.connect("fish.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fish (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    temperature REAL NOT NULL,
    aggression TEXT NOT NULL,
    size REAL NOT NULL
)
""")

conn.commit()

print("SQLite duomenų bazė ir lentelė 'fish' sėkmingai sukurta.")


def add_fish(name, temperature, aggression, size):
    cursor.execute("""
    INSERT INTO fish (name, temperature, aggression, size)
    VALUES (?, ?, ?, ?)
    """, (name, temperature, aggression, size))
    
    conn.commit()
    print(f"Žuvis '{name}' sėkmingai įrašyta į duomenų bazę.")

    cursor.execute("""
    SELECT * FROM fish
    WHERE name = ? AND temperature = ? AND aggression = ? AND size = ?
    ORDER BY id DESC
    LIMIT 1
    """, (name, temperature, aggression, size))
    
    result = cursor.fetchone()

    if result:
        print("Patikrinimas sėkmingas. Įrašas rastas duomenų bazėje:")
        print(result)
    else:
        print("Klaida: įrašo nepavyko rasti.")

    return result


def clear_fish_table():
    cursor.execute("DELETE FROM fish")
    conn.commit()


if __name__ == "__main__":
    add_fish("test_fish", 24.5, "test", 4.0)
    conn.close()