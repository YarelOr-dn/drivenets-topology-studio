from abc import ABC, abstractmethod
from typing import Dict

class AbstractOperation(ABC):
    @abstractmethod
    def __init__(self, params: Dict, validate_params: bool = True) -> None:
        pass

    @abstractmethod
    def _validate_params(self, params: Dict) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass
