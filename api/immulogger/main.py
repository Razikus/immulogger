from fastapi import FastAPI
from .database.immudb import ImmudbConfirmer
from .config.config import IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD
client = ImmudbConfirmer(IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD)
from .routers.authrouter import router as authRouter
from .routers.logrouter import router as logRouter

app = FastAPI(title = "Immulogger")

@app.on_event("startup")
async def onStartup():
    print(IMMUDB_URL, flush=True)
    with client as dbClient:
        dbClient.createTables()

app.include_router(authRouter, prefix="/api/v1/auth", tags=["authorization"])
app.include_router(logRouter, prefix="/api/v1/log", tags=["logs"])

