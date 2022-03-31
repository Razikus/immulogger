from fastapi import FastAPI
from .routers.authrouter import router as authRouter
from .routers.logrouter import router as logRouter
from .routers.userrouter import router as userRouter
from .serviceprovider import getServiceProvider

app = FastAPI(title = "Immulogger")

@app.on_event("startup")
async def onStartup():
    getServiceProvider().userProvider.populateDefaults()    
    with getServiceProvider().immudbConfirmer as dbClient:
        dbClient.createTables()

app.include_router(authRouter, prefix="/api/v1/auth", tags=["authorization"])
app.include_router(logRouter, prefix="/api/v1/log", tags=["logs"])
app.include_router(userRouter, prefix="/api/v1/user", tags=["users"])


