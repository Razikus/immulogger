from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Union
from .conditionbuilder import Condition
from .querybuilderutils import Builder, InvalidBuildState, ComparisionOperator

class SelectQueryState(Enum):
    START = auto()
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    CONDITION = auto()
    JOIN = auto()
    ORDERBY = auto()
    LIMIT = auto()
    BUILD = auto()

    def __str__(self):
        return self.name

class InsertQueryState(Enum):
    START = auto()
    INSERTINTO = auto()
    VALUES = auto()
    BUILD = auto()

    def __str__(self):
        return self.name
        

class BatchQueryBuilder(Builder):
    def __init__(self):
        self.queries = ["BEGIN TRANSACTION"]

    def addQuery(self, query: str):
        self.queries.append(query)
    
    def build(self):
        if(len(self.queries) == 1):
            raise InvalidBuildState("No queries added")
        self.queries.append("COMMIT")
        return "\n".join(self.queries)
    

class LogQueryBuilder(Builder):
    def __init__(self):
        self.constructing = ""
        self.currentState = SelectQueryState.START
        self.selectQueryPossibilities = {
            SelectQueryState.START: [SelectQueryState.SELECT],
            SelectQueryState.SELECT: [SelectQueryState.FROM],
            SelectQueryState.FROM: [SelectQueryState.JOIN, SelectQueryState.WHERE, SelectQueryState.ORDERBY, SelectQueryState.LIMIT, SelectQueryState.BUILD],
            SelectQueryState.JOIN: [SelectQueryState.JOIN, SelectQueryState.WHERE, SelectQueryState.ORDERBY, SelectQueryState.LIMIT, SelectQueryState.BUILD],
            SelectQueryState.WHERE: [SelectQueryState.CONDITION, SelectQueryState.ORDERBY, SelectQueryState.LIMIT, SelectQueryState.BUILD],
            SelectQueryState.CONDITION: [SelectQueryState.CONDITION, SelectQueryState.ORDERBY, SelectQueryState.LIMIT, SelectQueryState.BUILD],
            SelectQueryState.ORDERBY: [SelectQueryState.LIMIT, SelectQueryState.BUILD],
            SelectQueryState.LIMIT: [SelectQueryState.BUILD]
        }
        
    def _canSwitchToState(self, newState: SelectQueryState) -> bool:
        return newState in self.selectQueryPossibilities.get(self.currentState, [])

    def _switchToState(self, state: SelectQueryState) -> bool:
        if(not self._canSwitchToState(state)):
            raise InvalidBuildState(f"Cannot switch to state {state} from {self.currentState}")
        self.currentState = state
        return True

    def SELECT(self, *what):
        self._switchToState(SelectQueryState.SELECT)
        self.constructing = "SELECT " + ",".join(what)
        return self
    
    def FROM(self, *what):
        self._switchToState(SelectQueryState.FROM)
        self.constructing = self.constructing + " FROM " + ", ".join(what)
        return self
    
    def JOIN(self, what: str, field1: str, field2: str):
        self._switchToState(SelectQueryState.JOIN)
        self.constructing = self.constructing + f" INNER JOIN {what} ON {field1} = {field2}"
        return self

    def WHERE(self, what: str, comparedTo: Union[str, int], withOperator: ComparisionOperator = ComparisionOperator.eq):
        self._switchToState(SelectQueryState.WHERE)
        self.constructing = self.constructing + f" WHERE {what} {withOperator.value} {comparedTo}"
        return self

    def OR(self, what: str, equalsWhat: Union[str, int], withOperator: ComparisionOperator = ComparisionOperator.eq):
        self._switchToState(SelectQueryState.CONDITION)
        self.constructing = self.constructing + f" OR {what} {withOperator.value} {equalsWhat}"
        return self

    def WHERE_CONDITION(self, what: Condition):
        self._switchToState(SelectQueryState.WHERE)
        self.constructing = self.constructing + " WHERE " + what.render()
        return self

    def CONDITION(self, what: Condition):
        self._switchToState(SelectQueryState.CONDITION)
        self.constructing = self.constructing + what.render()
        return self

    def AND(self, what: str, equalsWhat: Union[str, int], withOperator: ComparisionOperator = ComparisionOperator.eq):
        self._switchToState(SelectQueryState.CONDITION)
        self.constructing = self.constructing + f" AND {what} {withOperator.value} {equalsWhat}"
        return self

    def ORDER_BY(self, what: str, method: str):
        self._switchToState(SelectQueryState.ORDERBY)
        self.constructing = self.constructing + f" ORDER BY {what} {method}"
        return self

    def LIMIT(self, what: int):
        self._switchToState(SelectQueryState.LIMIT)
        self.constructing = self.constructing + f" LIMIT {what}"
        return self

    def build(self):
        self._switchToState(SelectQueryState.BUILD)
        return self.constructing

class InsertWithParamsQueryBuilder(Builder):
    def __init__(self):
        self.constructing = ""
        self.currentState = InsertQueryState.START
        self.insertQueryPossibilities = {
            InsertQueryState.START: [InsertQueryState.INSERTINTO],
            InsertQueryState.INSERTINTO: [InsertQueryState.VALUES],
            InsertQueryState.VALUES: [InsertQueryState.VALUES, InsertQueryState.BUILD]
        }
        pass
        
    def _canSwitchToState(self, newState: InsertQueryState) -> bool:
        return newState in self.insertQueryPossibilities.get(self.currentState, [])

    def _switchToState(self, state: InsertQueryState) -> bool:
        if(not self._canSwitchToState(state)):
            raise InvalidBuildState(f"Cannot switch to state {state} from {self.currentState}")
        self.currentState = state
        return True

    def INSERT(self, what: str, *fields):
        self._switchToState(InsertQueryState.INSERTINTO)
        self.constructing = f"INSERT INTO {what} ({','.join(fields)})"
        return self
    
    def VALUES(self, index: int, *params):
        wasState = self.currentState
        self._switchToState(InsertQueryState.VALUES)
        paramList = []
        for param in params:
            paramList.append("@" + param + str(index))
        if(wasState == InsertQueryState.VALUES):
            self.constructing = self.constructing + f", ({','.join(paramList)})"
        else:
            self.constructing = self.constructing + f" VALUES({','.join(paramList)})"
        return self

    def VALUES_DIFFERENT_INDEXES(self, params: dict):
        wasState = self.currentState
        self._switchToState(InsertQueryState.VALUES)
        paramList = []
        for key, value in params.items():
            paramList.append("@" + key + str(value))
        if(wasState == InsertQueryState.VALUES):
            self.constructing = self.constructing + f", ({','.join(paramList)})"
        else:
            self.constructing = self.constructing + f" VALUES({','.join(paramList)})"
        return self

    def build(self):
        self._switchToState(InsertQueryState.BUILD)
        return self.constructing + ";"
