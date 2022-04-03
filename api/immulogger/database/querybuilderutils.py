from abc import ABC, abstractmethod
from enum import Enum

class ComparisionOperator(str, Enum):
    le = "<="
    ge = ">="
    gt = ">"
    lt = "<"
    eq = "="

class Builder(ABC):
    @abstractmethod
    def build(self):
        pass

class InvalidBuildState(Exception):
    pass