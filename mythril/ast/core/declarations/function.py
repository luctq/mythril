from abc import abstractmethod, ABCMeta
from typing import Dict, TYPE_CHECKING, List, Optional, Set, Union, Callable, Tuple
from enum import Enum

from mythril.ast.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
class FunctionType(Enum):
    NORMAL = 0
    CONSTRUCTOR = 1
    FALLBACK = 2
    RECEIVE = 3
    CONSTRUCTOR_VARIABLES = 10  # Fake function to hold variable declaration statements
    CONSTRUCTOR_CONSTANT_VARIABLES = 11  # Fake function to hold variable declaration statements


class Function(SourceMapping, metaclass=ABCMeta):
    def __init__(self, compilation_unit: "StaticCompilationUnit"):
        super().__init__()
        self._name: Optional[str] = None
        self._view: bool = False
        self._pure: bool = False

        self._id: Optional[str] = None

