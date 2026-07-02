import sqlite3
from datetime import date as date_type
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).parent / "gym.db"

mcp = FastMCP("gymlog")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            exercise TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            reps INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plan (
            id INTEGER PRIMARY KEY,
            week TEXT NOT NULL,
            day INTEGER NOT NULL,
            slot INTEGER NOT NULL,
            exercise TEXT NOT NULL,
            sets INTEGER NOT NULL,
            reps TEXT NOT NULL,
            weight_kg REAL
        )
    """)
    return conn


@mcp.tool()
def ping() -> str:
    """Confirms the gymlog server is alive."""
    return "gymlog server is running"


@mcp.tool()
def log_workout(entries: list[dict], date: str = "") -> str:
    """Log a workout session to the gym database.

    Args:
        entries: A list of sets. Each item must be a dict with keys:
            exercise (str, e.g. "bench press"),
            weight_kg (number),
            reps (int),
            sets (int, optional, default 1 — how many times this
            exact set was performed; expanded into that many rows).
        date: ISO date "YYYY-MM-DD". Defaults to today if omitted.

    Returns a confirmation with the number of sets logged.
    """
    workout_date = date or date_type.today().isoformat()
    conn = get_db()
    count = 0
    with conn:
        for e in entries:
            for _ in range(int(e.get("sets", 1))):
                conn.execute(
                    "INSERT INTO sets (date, exercise, weight_kg, reps) "
                    "VALUES (?, ?, ?, ?)",
                    (workout_date, e["exercise"].lower().strip(),
                     float(e["weight_kg"]), int(e["reps"])),
                )
                count += 1
    conn.close()
    return f"Logged {count} sets for {workout_date}."


@mcp.tool()
def get_day(date: str) -> str:
    """Get all sets logged on a given date.

    Args:
        date: ISO date "YYYY-MM-DD".
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT exercise, weight_kg, reps FROM sets WHERE date = ? ORDER BY id",
        (date,),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No sets logged on {date}."
    lines = [f"{ex}: {w}kg x {r}" for ex, w, r in rows]
    return f"Workout on {date}:\n" + "\n".join(lines)


@mcp.tool()
def get_plan(week: str = "") -> str:
    """Read the current training programme.

    Args:
        week: "A" or "B" for one week, or omit for both.

    Returns each day with its exercises, sets, reps and target weights.
    """
    conn = get_db()
    q = "SELECT week, day, slot, exercise, sets, reps, weight_kg FROM plan"
    params = ()
    if week:
        q += " WHERE week = ?"
        params = (week.upper(),)
    q += " ORDER BY week, day, slot"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    if not rows:
        return "No programme stored yet."
    out, current = [], None
    for wk, day, slot, ex, sets, reps, wt in rows:
        if (wk, day) != current:
            current = (wk, day)
            out.append(f"\n== Week {wk}, Day {day} ==")
        wt_str = f" @ {wt}kg" if wt is not None else ""
        out.append(f"  {slot}. {ex} — {sets}x{reps}{wt_str}")
    return "\n".join(out)


@mcp.tool()
def replace_day(week: str, day: int, exercises: list[dict]) -> str:
    """Replace one day of the training programme with a new exercise list.
    Other days are untouched. To edit part of a day, first call get_plan,
    then send back the full day with the desired changes.

    Args:
        week: "A" or "B".
        day: 1-4.
        exercises: Ordered list of dicts with keys:
            exercise (str), sets (int), reps (str, e.g. "8" or "8-10"),
            weight_kg (number, optional — target working weight).
    """
    week = week.upper()
    if week not in ("A", "B") or not 1 <= day <= 4:
        return "Error: week must be A or B, day must be 1-4."
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM plan WHERE week = ? AND day = ?", (week, day))
        for i, e in enumerate(exercises, start=1):
            conn.execute(
                "INSERT INTO plan (week, day, slot, exercise, sets, reps, weight_kg) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (week, day, i, e["exercise"].lower().strip(), int(e["sets"]),
                 str(e["reps"]),
                 float(e["weight_kg"]) if e.get("weight_kg") is not None else None),
            )
    conn.close()
    return f"Week {week} day {day} replaced with {len(exercises)} exercises."


if __name__ == "__main__":
    mcp.run()