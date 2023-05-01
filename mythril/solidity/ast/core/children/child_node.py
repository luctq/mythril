from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.solidity.ast.core.cfg.node import Node
    from mythril.solidity.ast.core.declarations import Function, Contract


class ChildNode:
    def __init__(self):
        super().__init__()
        self._node = None

    def set_node(self, node: "Node"):
        self._node = node

    @property
    def node(self) -> "Node":
        return self._node

    @property
    def function(self) -> "Function":
        return self.node.function

    @property
    def contract(self) -> "Contract":
        return self.node.function.contract

    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self.node.compilation_unit
