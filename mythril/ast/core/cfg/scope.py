from typing import List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from mythril.ast.core.cfg.node import Node
    from mythril.ast.core.declarations.function import Function
class Scope:
    def __init__(self, is_checked: bool, is_yul: bool, scope: Union["Scope", "Function"]):
        self.nodes: List["Node"] = []
        self.is_checked = is_checked
        self.is_yul = is_yul
        self.father = scope