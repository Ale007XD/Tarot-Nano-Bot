"""Docker healthcheck — verifies bot db is accessible."""
import sys
import sqlite3

try:
    con = sqlite3.connect("tarot.db", timeout=5)
    con.execute("SELECT 1")
    con.close()
    sys.exit(0)
except Exception as e:
    print(f"healthcheck failed: {e}", file=sys.stderr)
    sys.exit(1)
