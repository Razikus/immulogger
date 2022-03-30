import os


IMMUDB_HOST = os.environ.get("IMMUDB_HOST", "localhost")
IMMUDB_PORT = int(os.environ.get("IMMUDB_PORT", "3322"))
IMMUDB_LOGIN = os.environ.get("IMMUDB_LOGIN", "immudb")
IMMUDB_PASSWORD = os.environ.get("IMMUDB_PASSWORD", "immudb")

IMMUDB_URL = f"{IMMUDB_HOST}:{IMMUDB_PORT}"