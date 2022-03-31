from pydantic import BaseModel, constr
from typing import List, Optional
from abc import ABC, abstractmethod

from ..authutils.authutils import AllowedScope
from ..database.immudb import ImmudbConfirmer

class User(BaseModel):
    password_hash: constr(min_length=3, max_length=128)
    username: constr(min_length=3, max_length=64)
    privileges: List[AllowedScope] = []
    class Config:
        use_enum_values = True
    

class UserProvider(ABC):
    @abstractmethod
    def getUser(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    def addUser(self, user: User) -> bool:
        pass

    @abstractmethod
    def populateDefaults(self) -> bool:
        pass
        
    
class HardcodedUserProvider(UserProvider):
    def __init__(self):
        self.userDatabase = dict()
    
    def getUser(self, username: str) -> Optional[User]:
        return self.userDatabase.get(username, None)

    def addUser(self, user: User) -> bool:
        self.userDatabase[user.username] = User(username = user.username, password_hash  = user.password_hash, privileges = user.privileges)
        return True

    def populateDefaults(self) -> bool:
        self.userDatabase = {
            "admin": User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin", privileges =[AllowedScope.SEND_LOGS, AllowedScope.READ_LOGS, AllowedScope.USER_ADMIN]),
            "admin2": User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin2", privileges =[AllowedScope.SEND_LOGS]),
            "admin3": User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin3", privileges =[AllowedScope.READ_LOGS])
        }

        return True

class ImmudbUserProvider(UserProvider):
    def __init__(self, immuClient: ImmudbConfirmer):
        self.immuClient = immuClient

    def _generateKeyFromUsername(self, username: str) -> str:
        return f"USERS:{username}"

    def _generateBytesKeyFromUsername(self, username: str) -> bytes:
        return self._generateKeyFromUsername(username).encode("utf-8")
    
    def getUser(self, username: str) -> Optional[User]:
        with self.immuClient as client:
            try:
                what = client.getVerified(self._generateKeyFromUsername(username))
                if(what and what.value):
                    valueDecoded = what.value.decode("utf-8")
                    return User.parse_raw(valueDecoded)
                else:
                    return None
            except Exception as e:
                print(e)
                return None

    def addUser(self, user: User) -> bool:
        toJson = user.json().encode("utf-8")
        with self.immuClient as client:
            client.cryptoSet(self._generateKeyFromUsername(user.username), toJson)
            return True

    def populateDefaults(self) -> bool:
        if(not self.getUser("admin")):
            self.addUser(User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin", privileges =[AllowedScope.SEND_LOGS, AllowedScope.READ_LOGS, AllowedScope.USER_ADMIN]))
        if(not self.getUser("admin2")):
            self.addUser(User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin2", privileges =[AllowedScope.SEND_LOGS]))
        if(not self.getUser("admin3")):
            self.addUser(User(password_hash= "$2b$12$bL.Dm93w/6qErzSbWKKlquIMbzEpq8oXYDSQqo0RSTegna2hZ5dia", username = "admin3", privileges =[AllowedScope.READ_LOGS]))
        return True

