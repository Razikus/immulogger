
from pydantic import BaseModel, constr
from typing import Optional, List, Union

class AddLogBody(BaseModel):
    logContent: constr(max_length=4096, min_length=1)

class AddLogRequest(AddLogBody):
    tags: List[constr(max_length=64, min_length=1)] = []
    waitForIdentifier: bool = True

class AddLogsRequest(BaseModel):
    logs: List[Union[AddLogBody, constr(max_length=4096, min_length=1)]]
    tags: List[constr(max_length=64, min_length=1)] = []
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

class CountResponse(BaseModel):
    count: int