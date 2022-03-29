from fastapi import FastAPI
from .routers.authrouter import router as authRouter
from .routers.logrouter import router as logRouter
from .database.immudb import ImmudbConfirmer

app = FastAPI()

@app.on_event("startup")
async def onStartup():
    client = ImmudbConfirmer("localhost:3322", "immudb", "immudb")
    with client as dbClient:
        dbClient.createTables()

app.include_router(authRouter, prefix="/api/v1/auth", tags=["authorization"])
app.include_router(logRouter, prefix="/api/v1/log", tags=["logs"])

