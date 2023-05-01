from mythril.solidity.ast.core.source_mapping.source_mapping import SourceMapping
from typing import List, TYPE_CHECKING, Optional, Type, Union

from mythril.solidity.ast.core.solidity_types.user_defined_type import UserDefinedType
from mythril.solidity.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.solidity.ast.core.variables.local_variable import LocalVariable

if TYPE_CHECKING:
    from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit

class CustomError(SourceMapping):
    def __init__(self, compilation_unit: "StaticCompilationUnit"):
        super().__init__()
        self._name: str = ""
        self._parameters: List[LocalVariable] = []
        self._compilation_unit = compilation_unit

        self._solidity_signature: Optional[str] = None
        self._full_name: Optional[str] = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def parameters(self) -> List[LocalVariable]:
        return self._parameters

    def add_parameters(self, p: "LocalVariable"):
        self._parameters.append(p)

    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self._compilation_unit