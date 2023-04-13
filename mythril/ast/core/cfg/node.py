from enum import Enum
from typing import Union, List, Optional, TYPE_CHECKING, Set

from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.children.child_function import ChildFunction
from mythril.ast.core.declarations.function import Function
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.scope.scope import FileScope
from mythril.ast.core.cfg.scope import Scope
from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.variables.variable import Variable
from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.core.declarations.solidity_variables import SolidityVariable, SolidityFunction
from mythril.ast.astir.operations.operation import Operation
from mythril.ast.astir.convert import convert_expression
from mythril.ast.astir.operations.index import Index
from mythril.ast.astir.operations.member import Member
from mythril.ast.astir.operations.lvalue import OperationWithLValue
from mythril.ast.astir.operations.length import Length
from mythril.ast.astir.variables.reference import ReferenceVariable
from mythril.ast.astir.variables.constant import Constant
from mythril.ast.astir.variables.temporary import TemporaryVariable
from mythril.ast.astir.variables.tuple import TupleVariable
from mythril.exceptions import StaticException

if TYPE_CHECKING:
    from mythril.ast.astir.variables.variable import AstIRVariable
    from mythril.ast.core.compilation_unit import SlitherCompilationUnit
    from mythril.ast.utils.type_helpers import (
        InternalCallType,
        HighLevelCallType,
        LibraryCallType,
        LowLevelCallType,
    )

class NodeType(Enum):
    ENTRYPOINT = 0x0

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11  # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13  # Declaration of variable
    ASSEMBLY = 0x14
    IFLOOP = 0x15

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

        self._vars_written: List[Variable] = []
        self._vars_read: List[Variable] = []

        self._internal_calls: List["Function"] = []
        self._solidity_calls: List[SolidityFunction] = []
        self._high_level_calls: List["HighLevelCallType"] = []  # contains library calls
        self._library_calls: List["LibraryCallType"] = []
        self._low_level_calls: List["LowLevelCallType"] = []
        self._external_calls_as_expressions: List[Expression] = []
        self._internal_calls_as_expressions: List[Expression] = []
        self._state_vars_written: List[StateVariable] = []
        self._state_vars_read: List[StateVariable] = []
        self._solidity_vars_read: List[SolidityVariable] = []

        self._expression_vars_written: List[Expression] = []
        self._expression_vars_read: List[Expression] = []
        self._expression_calls: List[Expression] = []

        self._local_vars_read: List[LocalVariable] = []
        self._local_vars_written: List[LocalVariable] = []

        self._astir_vars: Set["AstIRVariable"] = set()  

        self._expression: Optional[Expression] = None
        self._variable_declaration: Optional[LocalVariable] = None

        self.scope: Union["Scope", "Function"] = scope
        self._irs: List[Operation] = []

        self._is_local_variable_declaration = False

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
    def variables_read_as_expression(self) -> List[Expression]:
        return self._expression_vars_read

    @variables_read_as_expression.setter
    def variables_read_as_expression(self, exprs: List[Expression]):
        self._expression_vars_read = exprs
    @property
    def variables_read(self) -> List[Variable]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def state_variables_read(self) -> List[StateVariable]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def local_variables_read(self) -> List[LocalVariable]:
        """
        list(LocalVariable): Local variables read
        """
        return list(self._local_vars_read)
    
    @property
    def variables_written(self) -> List[Variable]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_written(self) -> List[StateVariable]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def local_variables_written(self) -> List[LocalVariable]:
        """
        list(LocalVariable): Local variables written
        """
        return list(self._local_vars_written)

    @property
    def variables_written_as_expression(self) -> List[Expression]:
        return self._expression_vars_written

    @variables_written_as_expression.setter
    def variables_written_as_expression(self, exprs: List[Expression]):
        self._expression_vars_written = exprs
    
    @property
    def astir_variables(self) -> List["AstIRVariable"]:
        return list(self._astir_vars)
    
    @property
    def solidity_variables_read(self) -> List[SolidityVariable]:
        """
        list(SolidityVariable): State variables read
        """
        return list(self._solidity_vars_read)

    @property
    def calls_as_expression(self) -> List[Expression]:
        return list(self._expression_calls)

    @calls_as_expression.setter
    def calls_as_expression(self, exprs: List[Expression]):
        self._expression_calls = exprs
    
    @property
    def internal_calls(self) -> List["InternalCallType"]:
        """
        list(Function or SolidityFunction): List of internal/soldiity function calls
        """
        return list(self._internal_calls)

    @property
    def solidity_calls(self) -> List[SolidityFunction]:
        """
        list(SolidityFunction): List of Soldity calls
        """
        return list(self._solidity_calls)

    @property
    def high_level_calls(self) -> List["HighLevelCallType"]:
        """
        list((Contract, Function|Variable)):
        List of high level calls (external calls).
        A variable is called in case of call to a public state variable
        Include library calls
        """
        return list(self._high_level_calls)

    @property
    def library_calls(self) -> List["LibraryCallType"]:
        """
        list((Contract, Function)):
        Include library calls
        """
        return list(self._library_calls)

    @property
    def low_level_calls(self) -> List["LowLevelCallType"]:
        """
        list((Variable|SolidityVariable, str)): List of low_level call
        A low level call is defined by
        - the variable called
        - the name of the function (call/delegatecall/codecall)
        """
        return list(self._low_level_calls)

    @property
    def external_calls_as_expressions(self) -> List[Expression]:
        """
        list(CallExpression): List of message calls (that creates a transaction)
        """
        return self._external_calls_as_expressions

    @external_calls_as_expressions.setter
    def external_calls_as_expressions(self, exprs: List[Expression]):
        self._external_calls_as_expressions = exprs

    @property
    def internal_calls_as_expressions(self) -> List[Expression]:
        """
        list(CallExpression): List of internal calls (that dont create a transaction)
        """
        return self._internal_calls_as_expressions

    @internal_calls_as_expressions.setter
    def internal_calls_as_expressions(self, exprs: List[Expression]):
        self._internal_calls_as_expressions = exprs

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
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self.function.compilation_unit

    @property
    def node_id(self) -> int:
        """Unique node id."""
        return self._node_id

    @property
    def type(self) -> NodeType:
        """
        NodeType: type of the node
        """
        return self._node_type

    @type.setter
    def type(self, new_type: NodeType):
        self._node_type = new_type

    @property
    def expression(self) -> Optional[Expression]:
        """
        Expression: Expression of the node
        """
        return self._expression
    
    @property
    def irs(self) -> List[Operation]:
        """Returns the astIR representation

        return
            list(astIR.Operation)
        """
        return self._irs
    
    @staticmethod
    def _is_non_astir_var(var: Variable):
        return not isinstance(var, (Constant, ReferenceVariable, TemporaryVariable, TupleVariable))

    @staticmethod
    def _is_valid_astir_var(var: Variable):
        return isinstance(var, (ReferenceVariable, TemporaryVariable, TupleVariable))

    @property
    def is_local_variable_declaration(self) -> bool:
        return self._is_local_variable_declaration
    
    @is_local_variable_declaration.setter
    def is_local_variable_declaration(self, is_local_variable_declaration: bool):
        self._is_local_variable_declaration = is_local_variable_declaration


    def add_expression(self, expression: Expression, bypass_verif_empty: bool = False):
        assert self._expression is None or bypass_verif_empty
        self._expression = expression

    def add_variable_declaration(self, var: LocalVariable):
        assert self._variable_declaration is None
        self._variable_declaration = var
        if var.expression:
            self._vars_written += [var]
            self._local_vars_written += [var]
    
    @property
    def variable_declaration(self) -> Optional[LocalVariable]:
        """
        Returns:
            LocalVariable
        """
        return self._variable_declaration
    
    def astir_generation(self):
        print("\n===========START===============\n")
        print("self.expression", self.expression)
        print("self.expression", self.expression.__class__.__name__)
        if self.expression:
            expression = self.expression
            self._irs = convert_expression(expression, self)
        print("self._irs", self._irs)
        self._find_read_write_call()
        print("\n============END==============\n")

    def _find_read_write_call(self):  # pylint: disable=too-many-statements
        for ir in self.irs:

            self._astir_vars |= {v for v in ir.read if self._is_valid_astir_var(v)}
            if isinstance(ir, OperationWithLValue):
                var = ir.lvalue
                if var and self._is_valid_astir_var(var):
                    self._astir_vars.add(var)

            if not isinstance(ir, (Index, Member)):
                self._vars_read += [v for v in ir.read if self._is_non_astir_var(v)]
                for var in ir.read:
                    if isinstance(var, ReferenceVariable):
                        self._vars_read.append(var.points_to_origin)
            elif isinstance(ir, (Member, Index)):
                var = ir.variable_left if isinstance(ir, Member) else ir.variable_right
                if self._is_non_astir_var(var):
                    self._vars_read.append(var)
                if isinstance(var, ReferenceVariable):
                    origin = var.points_to_origin
                    if self._is_non_astir_var(origin):
                        self._vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, ReferenceVariable):
                    var = var.points_to_origin
                if var and self._is_non_astir_var(var) and not ir.node.is_local_variable_declaration:
                    self._vars_written.append(var)

        self._vars_read = list(set(self._vars_read))
        self._state_vars_read = [v for v in self._vars_read if isinstance(v, StateVariable)]
        self._local_vars_read = [v for v in self._vars_read if isinstance(v, LocalVariable)]
        self._solidity_vars_read = [v for v in self._vars_read if isinstance(v, SolidityVariable)]
        self._vars_written = list(set(self._vars_written))
        self._state_vars_written = [v for v in self._vars_written if isinstance(v, StateVariable)]
        self._local_vars_written = [v for v in self._vars_written if isinstance(v, LocalVariable)]
    
    def __str__(self):
        additional_info = ""
        if self.expression:
            additional_info += " " + str(self.expression)
        elif self.variable_declaration:
            additional_info += " " + str(self.variable_declaration)
        txt = str(self._node_type) + additional_info
        return txt

def link_nodes(node1: Node, node2: Node):
    node1.add_son(node2)
    node2.add_father(node1)