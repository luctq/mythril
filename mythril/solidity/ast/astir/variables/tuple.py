from typing import TYPE_CHECKING

from mythril.solidity.ast.core.children.child_node import ChildNode
from mythril.solidity.ast.astir.variables.variable import AstIRVariable

if TYPE_CHECKING:
    from mythril.solidity.ast.core.cfg.node import Node


class TupleVariable(ChildNode, AstIRVariable):
    def __init__(self, node: "Node", index=None):
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_astir_tuple
            node.compilation_unit.counter_astir_tuple += 1
        else:
            self._index = index

        self._node = node

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self):
        return f"TUPLE_{self.index}"

    def __str__(self):
        return self.name
