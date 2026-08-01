import sqlite3

connection = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL
)
""")

cursor.execute("SELECT COUNT(*) FROM tasks")

count = cursor.fetchone()[0]

if count == 0:
    cursor.executemany(
        "INSERT INTO tasks(title, done) VALUES(?, ?)",
        [
            ("Learn FastAPI", 0),
            ("Learn SQLite", 0),
            ("Push to GitHub", 0)
        ]
    )

connection.commit()
