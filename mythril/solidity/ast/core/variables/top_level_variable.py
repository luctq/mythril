from typing import Optional, TYPE_CHECKING

from mythril.solidity.ast.core.declarations.top_level import TopLevel
from mythril.solidity.ast.core.variables.variable import Variable

if TYPE_CHECKING:
    from mythril.solidity.ast.core.cfg.node import Node
    from mythril.solidity.ast.core.scope.scope import FileScope


class TopLevelVariable(TopLevel, Variable):
    def __init__(self, scope: "FileScope"):
        super().__init__()
        self._node_initialization: Optional["Node"] = None
        self.file_scope = scope