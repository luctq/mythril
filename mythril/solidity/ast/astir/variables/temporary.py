from typing import TYPE_CHECKING

from mythril.solidity.ast.core.children.child_node import ChildNode
from mythril.solidity.ast.core.variables.variable import Variable

if TYPE_CHECKING:
    from mythril.solidity.ast.core.cfg.node import Node


class TemporaryVariable(ChildNode, Variable):
    def __init__(self, node: "Node", index=None):
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_astir_temporary
            node.compilation_unit.counter_astir_temporary += 1
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
        return f"TMP_{self.index}"

    def __str__(self):
        return self.name
