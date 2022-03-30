from abc import ABC, abstractmethod

class Builder(ABC):
    @abstractmethod
    def build(self):
        pass

class BatchQueryBuilder(Builder):
    def __init__(self):
        self.queries = ["BEGIN TRANSACTION"]

    def addQuery(self, query: str):
        self.queries.append(query)
    
    def build(self):
        self.queries.append("COMMIT")
        return "\n".join(self.queries)


class LogQueryBuilder(Builder):
    def __init__(self):
        self.constructing = ""
        pass

    def SELECT(self, *what):
        self.constructing = "SELECT " + ",".join(what)
        return self
    
    def FROM(self, what: str):
        self.constructing = self.constructing + " FROM " + what
        return self
    
    def JOIN(self, what: str, field1: str, field2: str):
        self.constructing = self.constructing + f" INNER JOIN {what} ON {field1} = {field2}"
        return self

    def WHERE(self, what: str, equalsWhat: str):
        self.constructing = self.constructing + f" WHERE {what} = {equalsWhat}"
        return self

    def OR(self, what: str, equalsWhat: str):
        self.constructing = self.constructing + f" OR {what} = {equalsWhat}"
        return self

    def AND(self, what: str, equalsWhat: str):
        self.constructing = self.constructing + f" AND {what} = {equalsWhat}"
        return self

    def ORDER_BY(self, what: str, method: str):
        self.constructing = self.constructing + f" ORDER BY {what} {method}"
        return self

    def LIMIT(self, what: int):
        self.constructing = self.constructing + f" LIMIT {what}"
        return self

    def build(self):
        return self.constructing

class InsertWithParamsQueryBuilder(Builder):
    def __init__(self):
        self.constructing = ""
        pass

    def INSERT(self, what: str, *fields):
        self.constructing = f"INSERT INTO {what} ({','.join(fields)})"
        return self
    
    def VALUES(self, index: int, *params):
        paramList = []
        for param in params:
            paramList.append("@" + param + str(index))
        self.constructing = self.constructing + f" VALUES({','.join(paramList)})"
        return self

    def VALUES_DIFFERENT_INDEXES(self, params: dict):
        paramList = []
        for key, value in params.items():
            paramList.append("@" + key + str(value))
        self.constructing = self.constructing + f" VALUES({','.join(paramList)})"
        return self

    def build(self):
        return self.constructing + ";"
