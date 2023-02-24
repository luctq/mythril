from enum import Enum
from typing import Union, List, Optional

from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.children.child_function import ChildFunction
from mythril.ast.core.declarations.function import Function
from mythril.ast.core.scope.scope import FileScope
from mythril.ast.core.cfg.scope import Scope
from mythril.ast.core.expressions.expression import Expression
class NodeType(Enum):
    ENTRYPOINT = 0x0

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11  # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13  # Declaration of variable

    # Merging nodes
    # Can have phi IR operation
    ENDIF = 0x50  # ENDIF node source mapping points to the if/else body
    STARTLOOP = 0x51  # STARTLOOP node source mapping points to the entire loop body
    ENDLOOP = 0x52  # ENDLOOP node source mapping points to the entire loop body

    # Below the nodes have no expression
    # But are used to expression CFG structure

    # Absorbing node
    THROW = 0x20

    # Loop related nodes
    BREAK = 0x31
    CONTINUE = 0x32

    # Only modifier node
    PLACEHOLDER = 0x40

    TRY = 0x41
    CATCH = 0x42

    # Node not related to the CFG
    # Use for state variable declaration
    OTHER_ENTRYPOINT = 0x60

class Node(SourceMapping, ChildFunction): 
    def __init__(
        self,
        node_type: NodeType,
        node_id: int,
        scope: Union["Scope", "Function"],
        file_scope: "FileScope",
    ):
        super().__init__()
        self._node_type = node_type
        # TODO: rename to explicit CFG
        self._sons: List["Node"] = []
        self._fathers: List["Node"] = []

        self._expression: Optional[Expression] = None
        self.scope: Union["Scope", "Function"] = scope

    def add_father(self, father: "Node"):
        """Add a father node

        Args:
            father: father to add
        """
        self._fathers.append(father)

    def set_fathers(self, fathers: List["Node"]):
        """Set the father nodes

        Args:
            fathers: list of fathers to add
        """
        self._fathers = fathers

    @property
    def fathers(self) -> List["Node"]:
        """Returns the father nodes

        Returns:
            list(Node): list of fathers
        """
        return list(self._fathers)
    
    def add_son(self, son: "Node"):
        """Add a son node

        Args:
            son: son to add
        """
        self._sons.append(son) 
    def set_sons(self, sons: List["Node"]):
        """Set the son nodes

        Args:
            sons: list of fathers to add
        """
        self._sons = sons
    
    @property
    def sons(self) -> List["Node"]:
        """Returns the son nodes

        Returns:
            list(Node): list of sons
        """
        return list(self._sons)

    @property
    def expression(self) -> Optional[Expression]:
        """
        Expression: Expression of the node
        """
        return self._expression

    def add_expression(self, expression: Expression, bypass_verif_empty: bool = False):
        assert self._expression is None or bypass_verif_empty
        self._expression = expression

def link_nodes(node1: Node, node2: Node):
    node1.add_son(node2)
    node2.add_father(node1)