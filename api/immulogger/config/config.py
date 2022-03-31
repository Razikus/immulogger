import os


IMMUDB_HOST = os.environ.get("IMMUDB_HOST", "localhost")
IMMUDB_PORT = int(os.environ.get("IMMUDB_PORT", "3322"))
IMMUDB_LOGIN = os.environ.get("IMMUDB_LOGIN", "immudb")
IMMUDB_PASSWORD = os.environ.get("IMMUDB_PASSWORD", "immudb")

SECRET_KEY = os.environ.get("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")

IMMUDB_URL = f"{IMMUDB_HOST}:{IMMUDB_PORT}"