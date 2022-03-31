from pydantic import BaseModel, constr
from typing import List
from ...authutils.authutils import AllowedScope

class CreateUserRequest(BaseModel):
    username: constr(min_length=3, max_length=128)
    password: constr(min_length=3, max_length=128)
    privileges: List[AllowedScope]
    class Config:
        use_enum_values = True

class CreateUserResponse(BaseModel):
    status: bool