from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union, Set

from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.declarations.function_contract import FunctionContract
if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.scope.scope import FileScope
class Contract(SourceMapping):
    def __init__(self, compilation_unit: "StaticCompilationUnit", scope: "FileScope"):
        super().__init__()
        self._name: Optional[str] = None
        self._id: Optional[int] = None
        self._inheritance: List["Contract"] = []  

        # self._explicit_base_constructor_calls: List["Contract"] = []
        # self._enums: Dict[str, "EnumContract"] = {}
        # self._structures: Dict[str, "StructureContract"] = {}
        # self._events: Dict[str, "Event"] = {}
        # self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        # self._linearizedBaseContracts: List[int] = []
        # self._custom_errors: Dict[str, "CustomErrorContract"] = {}
        self.compilation_unit: "StaticCompilationUnit" = compilation_unit
        self.file_scope: "FileScope" = scope
    @property
    def name(self) -> str:
        """str: Name of the contract."""
        assert self._name
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def id(self) -> int:
        """Unique id."""
        assert self._id
        return self._id

    @id.setter
    def id(self, new_id):
        """Unique id."""
        self._id = new_id
