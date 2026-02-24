from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_NAME = "roomsync.db"

# =============================
# DATABASE INIT
# =============================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            bookedBy TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =============================
# HOME PAGE
# =============================
@app.route("/")
def home():
    return render_template("conference_booking.html")


# =============================
# GET BOOKINGS
# =============================
@app.route("/get_bookings", methods=["GET"])
def get_bookings():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM bookings ORDER BY date, start")
    rows = c.fetchall()
    conn.close()

    bookings = []
    for row in rows:
        bookings.append({
            "id": row["id"],
            "room": row["room"],
            "title": row["title"],
            "date": row["date"],
            "start": row["start"],
            "end": row["end"],
            "bookedBy": row["bookedBy"]
        })

    return jsonify(bookings)


# =============================
# BOOK ROOM (CLASH CHECK)
# =============================
@app.route("/book", methods=["POST"])
def book_room():
    data = request.get_json()

    room = data.get("room")
    title = data.get("title")
    date = data.get("date")
    start = data.get("start")
    end = data.get("end")
    bookedBy = data.get("bookedBy")

    if not all([room, title, date, start, end, bookedBy]):
        return jsonify({"success": False, "error": "Missing data"})

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # CLASH DETECTION
    c.execute("""
        SELECT * FROM bookings
        WHERE room = ?
        AND date = ?
        AND start < ?
        AND end > ?
    """, (room, date, end, start))

    clash = c.fetchone()

    if clash:
        conn.close()
        return jsonify({"success": False, "error": "Clash detected"})

    # INSERT NEW BOOKING
    c.execute("""
        INSERT INTO bookings (room, title, date, start, end, bookedBy)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (room, title, date, start, end, bookedBy))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =============================
# CANCEL BOOKING
# =============================
@app.route("/cancel/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =============================
# START SERVER (Render Uses Gunicorn)
# =============================
if __name__ == "__main__":
    init_db()
    app.run()
