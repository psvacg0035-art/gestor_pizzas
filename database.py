import sqlite3

def init_db():
    conn = sqlite3.connect('pizzas.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            telefono TEXT,
            sabor TEXT,
            cantidad INTEGER,
            precio REAL,
            total REAL,
            fecha TEXT,
            hora_entrega TEXT,
            estado TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
