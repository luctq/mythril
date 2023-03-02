from typing import List, Tuple, TYPE_CHECKING
from mythril.ast.core.declarations.top_level import TopLevel
from mythril.ast.core.declarations.function import Function

if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.scope.scope import FileScope

class FunctionTopLevel(Function, TopLevel):
    def __init__(self, compilation_unit: "StaticCompilationUnit", scope: "FileScope"):
        super().__init__(compilation_unit)
        self._scope: "FileScope" = scope