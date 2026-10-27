import sqlite3


db = sqlite3.connect("echo_assist.db")

cursor = db.cursor()

try:
    cursor.execute("PRAGMA foreign_keys=OFF")

    cursor.execute(
        "ALTER TABLE emergency_events "
        "RENAME TO emergency_events_old"
    )

    cursor.execute("""
        CREATE TABLE emergency_events (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            event_type VARCHAR(30) NOT NULL,
            latitude FLOAT,
            longitude FLOAT,
            status VARCHAR(20),
            created_at DATETIME,
            resolved_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        INSERT INTO emergency_events (
            id,
            user_id,
            event_type,
            latitude,
            longitude,
            status,
            created_at,
            resolved_at
        )
        SELECT
            id,
            user_id,
            event_type,
            latitude,
            longitude,
            status,
            created_at,
            resolved_at
        FROM emergency_events_old
    """)

    cursor.execute(
        "DROP TABLE emergency_events_old"
    )

    db.commit()

    print("Emergency table migrated successfully")

except Exception as error:
    db.rollback()
    print("Migration failed:", error)

finally:
    db.close()