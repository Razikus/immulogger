
from pydantic import BaseModel, conlist, constr
from typing import Optional, List, Union
    
logConstraint = constr(max_length=4096, min_length=1)
tagConstraint = constr(max_length=64, min_length=1)
identifierConstraint = constr(max_length=64, min_length=1)
shaConstraint = constr(max_length=64, min_length=1)

class VerifyRequest(BaseModel):
    logContent: logConstraint
    identifier: identifierConstraint

class VerifySHARequest(BaseModel):
    logSHA: shaConstraint
    identifier: identifierConstraint

class VerifyResponse(BaseModel):
    verified: bool

class AddLogBody(BaseModel):
    logContent: logConstraint

class AddLogRequest(AddLogBody):
    tags: conlist(item_type = tagConstraint, min_items = 0, max_items = 16) = []
    waitForIdentifier: bool = True

class AddLogsRequest(BaseModel):
    logs: conlist(item_type = Union[AddLogBody, logConstraint], min_items=1, max_items=10240)
    tags: conlist(item_type = tagConstraint, min_items = 0, max_items = 16) = []
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