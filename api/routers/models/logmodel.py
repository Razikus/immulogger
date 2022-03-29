
from pydantic import BaseModel
from typing import Optional, List, Union

class AddLogBody(BaseModel):
    logContent: str

class AddLogRequest(AddLogBody):
    tags: List[str] = []
    waitForIdentifier: bool = True

class AddLogsRequest(BaseModel):
    logs: List[Union[AddLogBody, str]]
    tags: List[str] = []
    waitForIdentifier: bool = True

class AddLogResponse(BaseModel):
    logId: str
    
class AddLogsResponse(BaseModel):
    logIds: List[str]


class LogResponse(BaseModel):
    log: str
    uniqueidentifier: str
    createdate: int
    tags: List[str] = []
    verified: bool = False
    
class LogsResponse(BaseModel):
    logs: List[LogResponse]