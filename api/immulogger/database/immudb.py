import binascii
from typing import List, Union
from immudb import ImmudbClient
import hashlib
import time
import uuid
from ..routers.models.logmodel import AddLogRequest, AddLogsRequest, AddLogBody, LogResponse
from .querybuilder import BatchQueryBuilder, ComparisionOperator, InsertQueryState, InsertWithParamsQueryBuilder, LogQueryBuilder
from .conditionbuilder import ConditionBuilder, Condition, ANDCondition, EmptyCondition, ORCondition


class ImmudbConfirmer:
    def __init__(self, url: str, username: str, password: str, keyPath: Union[str, None]):
        self.username = username
        self.password = password
        self.url = url
        self.keyPath = keyPath
        self.client = ImmudbClient(self.url, publicKeyFile=self.keyPath)
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
            return False

    def verifyLogSha(self, logSHA: str, logIdentifier: str) -> bool:
        try:
            verifiedSha = self.getVerified(logIdentifier)
            strigified = binascii.hexlify(verifiedSha.value).decode("utf-8")
            return logSHA == strigified and verifiedSha.verified == True
        except Exception as e:
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

    def getQueriesForAddingTags(self, startsFrom: int, logId: str, tags: List[str], insertQuery: InsertWithParamsQueryBuilder = None):
        if(not insertQuery):
            insertQuery = InsertWithParamsQueryBuilder()
        additionalParams = dict()
        tags = list(set(tags))
        if(insertQuery.currentState is InsertQueryState.START):
            insertQuery.INSERT("TAGS", "uniqueidentifier", "tag")
        lastIndex = 0
        for index in range(0, len(tags)):
            tagParam = f"tag{index + startsFrom}"
            uniqueParam = f"uniqueidentifier{index + startsFrom}"
            additionalParams[tagParam] = tags[index]
            additionalParams[uniqueParam] = logId
            insertQuery.VALUES(index + startsFrom, "uniqueidentifier", "tag")
            lastIndex = index
        return lastIndex + startsFrom + 1, additionalParams, insertQuery
        

    def addLog(self, identifier: str, content: str, timeReceived: int, tags: List[str]):
        params = {
            "log0": content,
            "uniqueidentifier0": identifier,
            "createdate0": timeReceived
        }
        batchQuery = BatchQueryBuilder()
        query = InsertWithParamsQueryBuilder().INSERT("LOGS", "log", "uniqueidentifier", "createdate").VALUES(0, "log", "uniqueidentifier", "createdate").build()
        batchQuery.addQuery(query)
        if(len(tags) > 0):
            lastIndex, additionalParams, tagsQueries = self.getQueriesForAddingTags(0, identifier, tags)
            params = {**params, **additionalParams}
            batchQuery.addQuery(tagsQueries.build())

        return self.client.sqlExec(batchQuery.build(), params)

    def processLogs(self, logs: List[Union[AddLogBody, str]], timeReceived: int, tags: List[str]):
        params = dict()
        identifiers = []
        confirmations = dict()
        batchQueryBuilder = BatchQueryBuilder()
        logsInsertQueryBuilder = InsertWithParamsQueryBuilder()
        tagsInsertQueryBuilder = InsertWithParamsQueryBuilder()
        logsInsertQueryBuilder.INSERT("LOGS", "log", "uniqueidentifier", "createdate")
        lastTagsIndex = 0
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
            logsInsertQueryBuilder.VALUES(index, "log", "uniqueidentifier", "createdate")
            confirmations[identifier.encode("utf-8")] = self.makeSha256(content.encode("utf-8"))
            if(len(tags) > 0):
                lastTagsIndex, additionalParams, tagsQueries = self.getQueriesForAddingTags(lastTagsIndex, identifier, tags, tagsInsertQueryBuilder)
                params = {**params, **additionalParams}
        
        batchQueryBuilder.addQuery(logsInsertQueryBuilder.build())
        if(len(tags) > 0):
            batchQueryBuilder.addQuery(tagsInsertQueryBuilder.build())

        self.client.sqlExec(batchQueryBuilder.build(), params)
        self.client.setAll(confirmations)
        return identifiers

    def processLogRequest(self, newLog: AddLogRequest):
        result = self.processLogs([newLog.logContent], int(time.time() * 1000), newLog.tags)
        if(len(result) > 0):
            return result[0]
        else:
            return None

    def _chunks(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def processLogsRequest(self, newLogs: AddLogsRequest):
        # Internal constraint of immudb. max 512 lines in one TX.
        allIdentifiers = []
        chunks = int(1024 / (len(newLogs.tags) + 1))
        for chunk in self._chunks(newLogs.logs, chunks):
            allIdentifiers.extend(self.processLogs(chunk, int(time.time() * 1000), newLogs.tags))
        return allIdentifiers

    def getTags(self, identifier: str):
        result = self.client.sqlQuery("SELECT tag FROM TAGS WHERE uniqueidentifier=@identifier", {"identifier": identifier})
        return [item[0] for item in result]        

    def _createLogQuery(self, lastId: int, limit: int, tagsFilter: List[str]):
        builder = LogQueryBuilder()
        builder = builder.SELECT("log", "uniqueidentifier", "createdate", "id").FROM("LOGS")
        query = ""
        additionalParams = dict()
        conditionBuilder = ConditionBuilder()

        if(len(tagsFilter) > 0):
            builder.JOIN("TAGS", "LOGS.uniqueidentifier", "TAGS.uniqueidentifier")
            for index in range(0, len(tagsFilter)):
                tagIdentifier = f"tag{index}"
                additionalParams[tagIdentifier] = tagsFilter[index]
                conditionBuilder.OR(Condition("TAGS.tag", ComparisionOperator.eq, f"@{tagIdentifier}"))
        if(limit >= 1):
            builded = conditionBuilder.build()
            if(not type(builded) == EmptyCondition):
                builder.WHERE_CONDITION(conditionBuilder.build())
            builder.ORDER_BY("id", "DESC")
            builder.LIMIT(limit)
        else:
            if(lastId > 0):
                conditionBuilder.LEFT_AND(Condition("id", ComparisionOperator.lt, lastId))
            builded = conditionBuilder.build()
            if(not type(builded) == EmptyCondition):
                builder.WHERE_CONDITION(conditionBuilder.build())
                
            builder.ORDER_BY("id", "DESC")
            builder.LIMIT(256)
        query = builder.build()
        return additionalParams, query

    def getLastLogs(self, limit: int, verify: bool = False, tagsFilter: List[str] = []):
        formattedResult = []
        hasNext = True
        lastId = 0
        while hasNext:
            if(limit >= 1):
                hasNext = False
            additionalParams, query = self._createLogQuery(lastId, limit, tagsFilter)
            result = self.client.sqlQuery(query, additionalParams)

            distinctWorkaroundDict = dict()
            if(len(result) == 0):
                hasNext = False
                continue
            lastId = result[-1][3]
            for item in result:
                verified = False
                if(verify):
                    verified = self.verifyLogContent(item[0], item[1])

                # I couldn't find possibility to fetch tags in one query. Strange behaviour of GROUP BY and select
                # DISTINCT not implemented in SQL Querys
                identifier = item[1]
                tags = self.getTags(identifier)
                if(len(tagsFilter) > 0):
                    if(all(tag in tags for tag in tagsFilter)):
                        if(distinctWorkaroundDict.get(identifier, False) == False):
                            distinctWorkaroundDict[identifier] = True
                            formattedResult.append(
                                LogResponse(log = item[0], uniqueidentifier = identifier, createdate = item[2], tags = tags, verified = verified)
                            )
                else:
                    formattedResult.append(
                        LogResponse(log = item[0], uniqueidentifier = identifier, createdate = item[2], tags = tags, verified = verified)
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
            self.client.sqlExec("""CREATE INDEX ON Tags(tag);""")
            self.client.sqlExec("""CREATE UNIQUE INDEX ON Logs(uniqueidentifier);""")
        except:
            pass
        self.client.sqlExec("""
        CREATE TABLE IF NOT EXISTS Tags(
            uniqueidentifier VARCHAR[64] NOT NULL, 
            tag VARCHAR[64] NOT NULL,
            PRIMARY KEY (uniqueidentifier, tag)
        )""")




    