import sqlite3
from sqlite3 import IntegrityError, OperationalError

connection = sqlite3.connect("tutorial.db")

cursor = connection.cursor()

cursor.executescript(
    """
    BEGIN;
    CREATE TABLE IF NOT EXISTS tasks (
        hash TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        type INTEGER NOT NULL
    ) WITHOUT ROWID;
    COMMIT;
"""
)

d = {"hash": "1111", "status": "completed", "type": 12}

cursor.execute(
    """INSERT INTO tasks (hash, status, type) VALUES (:hash, :status, :type)
    ON CONFLICT(hashh) DO UPDATE SET
        status=:status,
        type=:type;
    """,
    d,
)
connection.commit()
result = cursor.execute("SELECT * FROM tasks")

from pprint import pprint

pprint(result.fetchall())
