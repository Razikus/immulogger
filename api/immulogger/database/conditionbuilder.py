from __future__ import annotations
from .querybuilderutils import Builder, InvalidBuildState, ComparisionOperator
from abc import ABC, abstractmethod

from typing import List, Union

class ConditionBuilder(Builder):
    def __init__(self):
        self.condition = None

    def OR(self, condition: Condition):
        if(not self.condition):
            self.condition = condition
        else:
            self.condition = ORCondition(self.condition, condition)

    def AND(self, condition: Condition):
        if(not self.condition):
            self.condition = condition
        else:
            self.condition = ANDCondition(self.condition, condition)

    def LEFT_AND(self, condition: Condition):
        if(not self.condition):
            self.condition = condition
        else:
            self.condition = ANDCondition(condition, self.condition)


    def build(self):
        if(self.condition == None):
            return EmptyCondition()
        else:
            return self.condition

class Renderable(ABC):
    @abstractmethod
    def render(self):
        pass

class Condition(Renderable):
    def __init__(self, what: Union[str,int], operator: ComparisionOperator, comparedTo: Union[str,int]):
        self.what = what
        self.operator = operator
        self.comparedTo = comparedTo

    def render(self):
        return f"{self.what} {self.operator.value} {self.comparedTo}"

class EmptyCondition(Renderable):
    def render(self):
        return ""

class ANDCondition(Condition):
    def __init__(self, condition1: Condition, condition2: Condition):
        self.condition1 = condition1
        self.condition2 = condition2

    def render(self):
        return f"({self.condition1.render()} AND {self.condition2.render()})"

class ORCondition(Condition):
    def __init__(self, condition1: Condition, condition2: Condition):
        self.condition1 = condition1
        self.condition2 = condition2

    def render(self):
        return f"({self.condition1.render()} OR {self.condition2.render()})"