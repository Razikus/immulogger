from typing import List
from fastapi import APIRouter, BackgroundTasks, Query, Security
from fastapi import Depends
from pydantic import conint

from ..authutils.authutils import AllowedScope
from .authrouter import get_current_user
from ..database.immudb import ImmudbConfirmer
from .models.logmodel import AddLogRequest, AddLogResponse, AddLogsRequest, AddLogsResponse, CountResponse, LogsResponse, VerifyRequest, VerifyResponse, VerifySHARequest
from ..serviceprovider import getServiceProvider
router = APIRouter()

async def getImmudbClient() -> ImmudbConfirmer:
    return getServiceProvider().immudbConfirmer

async def withWrapper(withWhat, callWhat, withWhatParam):
    with withWhat as withWhatOpened:
        func = getattr(withWhatOpened, callWhat)
        print("Background wrapper task ended", func(withWhatParam))

@router.put("/create", summary="Add log", response_model=AddLogResponse)
async def addLog(logRequest: AddLogRequest, background_tasks: BackgroundTasks, confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.SEND_LOGS.value])):
    if(logRequest.waitForIdentifier):
        with confirmer as client:
            return AddLogResponse(logId = client.processLogRequest(logRequest))
    else:
        background_tasks.add_task(withWrapper, confirmer, "processLogRequest", logRequest)
        return AddLogResponse(logId = "NOT_WAITING")

@router.put("/batchcreate", summary="Add logs", response_model=AddLogsResponse)
async def addLogs(logRequest: AddLogsRequest, background_tasks: BackgroundTasks, confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.SEND_LOGS.value])):
    if(logRequest.waitForIdentifier):
        with confirmer as client:   
            return AddLogsResponse(logIds = client.processLogsRequest(logRequest))
    else:
        background_tasks.add_task(withWrapper, confirmer, "processLogsRequest", logRequest)
        return AddLogsResponse(logIds = ["NOT_WAITING"])

@router.get("/get", summary="Get logs", response_model=LogsResponse)
async def getLogs(limit: conint(le = 1000) = -1, verify: bool = False, tags: List[str] = Query([]), confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.READ_LOGS.value])):
    with confirmer as client:
        return LogsResponse(logs = client.getLastLogs(limit, verify, tags))

@router.get("/count", summary="Count logs", response_model=CountResponse)
async def countLogs(confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.READ_LOGS.value])):
    with confirmer as client:
        return CountResponse(count = client.getLogCount())

@router.post("/verify", summary="Log content verify", response_model=VerifyResponse)
async def verifyLogContent(body: VerifyRequest, confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.READ_LOGS.value])):
    with confirmer as client:
        return VerifyResponse(verified = client.verifyLogContent(body.logContent, body.identifier))

@router.post("/verifySha", summary="Log SHA256 verify", response_model=VerifyResponse)
async def verifyLogContent(body: VerifySHARequest, confirmer: ImmudbConfirmer = Depends(getImmudbClient), current_user = Security(get_current_user, scopes=[AllowedScope.READ_LOGS.value])):
    with confirmer as client:
        return VerifyResponse(verified = client.verifyLogSha(body.logSHA, body.identifier))