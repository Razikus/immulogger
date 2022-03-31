from fastapi import APIRouter, Security
from fastapi import Depends
from ..authutils.authutils import AllowedScope, get_password_hash
from ..database.userprovider import User, UserProvider
from .authrouter import get_current_user
from .models.usermodel import CreateUserResponse, CreateUserRequest
from ..serviceprovider import getServiceProvider
router = APIRouter()

async def getUserProvider() -> UserProvider:
    return getServiceProvider().userProvider

@router.put("/create", summary="Creates User", response_model=CreateUserResponse)
async def createUser(userRequest: CreateUserRequest, userProvider: UserProvider = Depends(getUserProvider), current_user = Security(get_current_user, scopes=[AllowedScope.USER_ADMIN.value])):
    password_hashed = get_password_hash(userRequest.password)
    newUser = User(password_hash = password_hashed, username = userRequest.username, privileges = userRequest.privileges)
    return CreateUserResponse(status = userProvider.addUser(newUser))
    
