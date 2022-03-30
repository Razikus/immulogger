from typing import List, Union
from immudb import ImmudbClient
import hashlib
import time
import json
import uuid
from ..routers.models.logmodel import AddLogRequest, AddLogsRequest, AddLogBody, LogResponse
from .querybuilder import BatchQueryBuilder, InsertWithParamsQueryBuilder, LogQueryBuilder


class ImmudbConfirmer:
    def __init__(self, url: str, username: str, password: str):
        self.username = username
        self.password = password
        self.url = url
        self.client = ImmudbClient(self.url)
        self.logged = False
        self.lastLogged = 0

    def __enter__(self):
        now = time.time()
        if(now > self.lastLogged + 30 * 60):
            self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        
        pass

    def generateIdentifier(self, logData: str):
        shaFrom = self.makeStrSha256(logData.encode("utf-8"))
        return str(uuid.uuid4()) + shaFrom[0:10]

    def login(self):
        self.client.login(self.username, self.password)
        self.lastLogged = time.time()
        self.logged = True

    def logout(self):
        self.client.logout()
        self.logged = False

    def cryptoSet(self, key: str, value: bytes):
        what = self.client.verifiedSet(key.encode("utf-8"), value)
        return what

    def getVerified(self, id: str) -> bytes:
        return self.client.verifiedGet(id.encode("utf-8"))

    def verifyLogContent(self, log: str, logIdentifier: str) -> bool:
        try:
            verifiedSha = self.getVerified(logIdentifier)
            toSha = log.encode("utf-8")
            shaFrom = self.makeSha256(toSha)
            return shaFrom == verifiedSha.value and verifiedSha.verified == True
        except Exception as e:
            print("Cannot verify", e)
            return False


    def makeSha256(self, fromWhat: bytes):
        builder = hashlib.sha256()
        builder.update(fromWhat)
        return builder.digest()

    def makeStrSha256(self, fromWhat: bytes):
        builder = hashlib.sha256()
        builder.update(fromWhat)
        return builder.hexdigest()


    def storeConfirmation(self, id: str, log: str):
        loghash = self.makeSha256(log.encode("utf-8"))
        return self.cryptoSet(id, loghash)

    def addTagsFor(self, logId: str, tags: List[str]):
        additionalParams = dict()
        batchQueryBuilder = BatchQueryBuilder()
        tags = list(set(tags))
        for index in range(0, len(tags)):
            tagParam = f"tag{index}"
            uniqueParam = f"uniqueidentifier{index}"
            additionalParams[tagParam] = tags[index]
            additionalParams[uniqueParam] = logId
            query = InsertWithParamsQueryBuilder().INSERT("TAGS", "uniqueidentifier", "tag").VALUES(index, "uniqueidentifier", "tag").build()
            batchQueryBuilder.addQuery(query)
        return self.client.sqlExec(batchQueryBuilder.build(), additionalParams)

    def addLog(self, identifier: str, content: str, timeReceived: int):
        params = {
            "log0": content,
            "uniqueidentifier0": identifier,
            "createdate0": timeReceived
        }
        query = InsertWithParamsQueryBuilder().INSERT("LOGS", "log", "uniqueidentifier", "createdate").VALUES(0, "log", "uniqueidentifier", "createdate").build()
        return self.client.sqlExec(query, params)

    def processLogs(self, logs: List[Union[AddLogBody, str]], timeReceived: int):
        params = dict()
        identifiers = []
        confirmations = []
        batchQueryBuilder = BatchQueryBuilder()
        for index in range(0, len(logs)):
            item = logs[index]
            if(type(item) == AddLogBody):
                content = item.logContent
            else:
                content = item
            params[f"log{index}"] = content
            identifier = self.generateIdentifier(content)
            identifiers.append(identifier)
            params[f"uniqueidentifier{index}"] = identifier
            params[f"createdate{index}"] = timeReceived
            query = InsertWithParamsQueryBuilder().INSERT("LOGS", "log", "uniqueidentifier", "createdate").VALUES(index, "log", "uniqueidentifier", "createdate").build()
            batchQueryBuilder.addQuery(query)
            confirmations.append([identifier, self.makeSha256(content.encode("utf-8"))])
        self.client.sqlExec(batchQueryBuilder.build(), params)
        for item in confirmations:
            self.cryptoSet(item[0], item[1])
        return identifiers

    def processTagsForLogs(self, tags: List[str], identifiers: List[str]):
        additionalParams = dict()
        batchQueryBuilder = BatchQueryBuilder()
        tags = list(set(tags))
        for identifierIndex in range(0, len(identifiers)):
            for index in range(0, len(tags)):
                tagParam = f"tag{index}"
                uniqueParam = f"uniqueidentifier{identifierIndex}"
                additionalParams[tagParam] = tags[index]
                additionalParams[uniqueParam] = identifiers[identifierIndex]
                query = InsertWithParamsQueryBuilder().INSERT("TAGS", "uniqueidentifier", "tag").VALUES_DIFFERENT_INDEXES({"uniqueidentifier": identifierIndex, "tag": index}).build()
                batchQueryBuilder.addQuery(query)
        return self.client.sqlExec(batchQueryBuilder.build(), additionalParams)


    def processLogRequest(self, newLog: AddLogRequest):
        identifier = self.generateIdentifier(newLog.logContent)
        result = self.addLog(identifier, newLog.logContent, int(time.time() * 1000))
        self.storeConfirmation(identifier, newLog.logContent)
        if(len(newLog.tags) > 0):
            self.addTagsFor(identifier, newLog.tags)
        return identifier

    def processLogsRequest(self, newLogs: AddLogsRequest):
        identifiers = self.processLogs(newLogs.logs, int(time.time() * 1000))
        if(len(newLogs.tags) > 0):
            self.processTagsForLogs(newLogs.tags, identifiers)
        return identifiers

    def getTags(self, identifier: str):
        result = self.client.sqlQuery("SELECT tag FROM TAGS WHERE uniqueidentifier=@identifier", {"identifier": identifier})
        return [item[0] for item in result]
        

    def getLastLogs(self, limit: int, verify: bool = False, tagsFilter: List[str] = []):
        builder = LogQueryBuilder()
        builder = builder.SELECT("log", "uniqueidentifier", "createdate").FROM("LOGS")
        query = ""
        additionalParams = dict()

        if(len(tagsFilter) > 0):
            builder.JOIN("TAGS", "LOGS.uniqueidentifier", "TAGS.uniqueidentifier")
            for index in range(0, len(tagsFilter)):
                tagIdentifier = f"tag{index}"
                additionalParams[tagIdentifier] = tagsFilter[index]
                if(index == 0):
                    builder.WHERE("TAGS.tag", f"@{tagIdentifier}")
                else:
                    builder.OR("TAGS.tag", f"@{tagIdentifier}")  
        builder.ORDER_BY("id", "DESC")      
        if(limit >=1):
            builder.LIMIT(limit)
        query = builder.build()

        result = self.client.sqlQuery(query, additionalParams)
        formattedResult = []
        for item in result:
            verified = False
            if(verify):
                verified = self.verifyLogContent(item[0], item[1])

            # I couldn't find possibility to fetch tags in one query. Strange behaviour of GROUP BY
            tags = self.getTags(item[1])
            formattedResult.append(
                LogResponse(log = item[0], uniqueidentifier = item[1], createdate = item[2], tags = tags, verified = verified)
            )
        return formattedResult

    def getLogCount(self):
        toRet = self.client.sqlQuery("SELECT COUNT() FROM LOGS")
        if(len(toRet) > 0 and len(toRet[0]) > 0):
            return toRet[0][0]
        else:
            return -1

    # Move to external migration
    def createTables(self):
        self.client.sqlExec("""CREATE TABLE IF NOT EXISTS Logs(
            id INTEGER AUTO_INCREMENT, 
            log VARCHAR[4096] NOT NULL, 
            uniqueidentifier VARCHAR[64] NOT NULL, 
            createdate INTEGER NOT NULL, 
            PRIMARY KEY (id)
        )""")
        try:
            self.client.sqlExec("""CREATE INDEX ON Logs(id);""")
            self.client.sqlExec("""CREATE UNIQUE INDEX ON Logs(uniqueidentifier);""")
        except:
            pass
        self.client.sqlExec("""
        CREATE TABLE IF NOT EXISTS Tags(
            uniqueidentifier VARCHAR[64] NOT NULL, 
            tag VARCHAR[64] NOT NULL,
            PRIMARY KEY (uniqueidentifier, tag)
        )""")




    