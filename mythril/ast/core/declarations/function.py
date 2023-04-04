from abc import abstractmethod, ABCMeta
from typing import Dict, TYPE_CHECKING, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from itertools import groupby

from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.core.scope.scope import FileScope
from mythril.ast.core.cfg.scope import Scope
from mythril.ast.core.variables.variable import Variable
from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.core.declarations.solidity_variables import SolidityVariable, SolidityFunction

if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.cfg.node import Node, NodeType
    from mythril.ast.utils.type_helpers import (
            InternalCallType, 
            LowLevelCallType, 
            HighLevelCallType, 
            LibraryCallType)
    from mythril.ast.core.declarations.contract import Contract

class ModifierStatements:
    def __init__(
        self,
        modifier: Union["Contract", "Function"],
        entry_point: "Node",
        nodes: List["Node"],
    ):
        self._modifier = modifier
        self._entry_point = entry_point
        self._nodes = nodes

    @property
    def modifier(self) -> Union["Contract", "Function"]:
        return self._modifier

    @property
    def entry_point(self) -> "Node":
        return self._entry_point

    @entry_point.setter
    def entry_point(self, entry_point: "Node"):
        self._entry_point = entry_point

    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @nodes.setter
    def nodes(self, nodes: List["Node"]):
        self._nodes = nodes

class FunctionType(Enum):
    NORMAL = 0
    CONSTRUCTOR = 1
    FALLBACK = 2
    RECEIVE = 3
    CONSTRUCTOR_VARIABLES = 10  # Fake function to hold variable declaration statements
    CONSTRUCTOR_CONSTANT_VARIABLES = 11  # Fake function to hold variable declaration statements

class FunctionLanguage(Enum):
    Solidity = 0
    Yul = 1
    Vyper = 2

class Function(SourceMapping, metaclass=ABCMeta):
    def __init__(self, compilation_unit: "StaticCompilationUnit"):
        super().__init__()
        self._internal_scope: List[str] = []
        self._name: Optional[str] = None
        self._view: bool = False
        self._pure: bool = False
        self._payable: bool = False
        self._visibility: Optional[str] = None
        self._nodes: List["Node"] = []
        self._parameters: List["LocalVariable"] = []
        self._parameters_src: SourceMapping = SourceMapping()
        self._returns: List["LocalVariable"] = []
        self._returns_src: SourceMapping = SourceMapping()

        self._function_type: Optional[FunctionType] = None

        self._all_internals_calls: Optional[List["InternalCallType"]] = None
        self._all_high_level_calls: Optional[List["HighLevelCallType"]] = None
        self._all_library_calls: Optional[List["LibraryCallType"]] = None
        self._all_low_level_calls: Optional[List["LowLevelCallType"]] = None
        self._all_solidity_calls: Optional[List["SolidityFunction"]] = None

        self._variables: Dict[str, "LocalVariable"] = {}
        self._vars_read: List["Variable"] = []
        self._vars_written: List["Variable"] = []
        self._state_vars_read: List["StateVariable"] = []
        self._vars_read_or_written: List["Variable"] = []
        self._solidity_vars_read: List["SolidityVariable"] = []
        self._state_vars_written: List["StateVariable"] = []
        self._internal_calls: List["InternalCallType"] = []
        self._solidity_calls: List["SolidityFunction"] = []
        self._low_level_calls: List["LowLevelCallType"] = []
        self._high_level_calls: List["HighLevelCallType"] = []
        self._library_calls: List["LibraryCallType"] = []
        self._full_name: Optional[str] = None
        self._signature: Optional[Tuple[str, List[str], List[str]]] = None
        self._solidity_signature: Optional[str] = None
        self._signature_str: Optional[str] = None
        self._canonical_name: Optional[str] = None
        self._is_protected: Optional[bool] = None
        self._is_implemented: Optional[bool] = None
        self._modifiers: List[ModifierStatements] = []
        self._is_shadowed: bool = False
        self._shadows: bool = False

        self.compilation_unit: "StaticCompilationUnit" = compilation_unit

        self._counter_nodes = 0

        # Assume we are analyzing Solidity by default
        self.function_language: FunctionLanguage = FunctionLanguage.Solidity
        self._id: Optional[str] = None
    

    @property
    def name(self) -> str:
        """
        str: function name
        """
        if self._name == "" and self._function_type == FunctionType.CONSTRUCTOR:
            return "constructor"
        if self._function_type == FunctionType.FALLBACK:
            return "fallback"
        if self._function_type == FunctionType.RECEIVE:
            return "receive"
        if self._function_type == FunctionType.CONSTRUCTOR_VARIABLES:
            return "ConstructorVariables"
        if self._function_type == FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES:
            return "ConstructorConstantVariables"
        return self._name
    @property
    def is_checked(self) -> bool:
        """
        Return true if the overflow are enabled by default


        :return:
        """

        return self.compilation_unit.solc_version >= "0.8.0"

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    @property
    def nodes(self) -> List["Node"]:
        """
        list(Node): List of the nodes
        """
        return list(self._nodes)

    @nodes.setter
    def nodes(self, nodes: List["Node"]):
        self._nodes = nodes
    @property
    def is_shadowed(self) -> bool:
        return self._is_shadowed

    @is_shadowed.setter
    def is_shadowed(self, is_shadowed):
        self._is_shadowed = is_shadowed

    @property
    def is_implemented(self) -> bool:
        """
        bool: True if the function is implemented
        """
        return self._is_implemented

    @is_implemented.setter
    def is_implemented(self, is_impl: bool):
        self._is_implemented = is_impl

    @property
    def id(self) -> Optional[str]:
        """
        Return the ID of the funciton. For Solidity with compact-AST the ID is the reference ID
        For other, the ID is None

        :return:
        :rtype:
        """
        return self._id

    @id.setter
    def id(self, new_id: str):
        self._id = new_id

    @property
    @abstractmethod
    def file_scope(self) -> "FileScope":
        pass

    @property
    def function_type(self) -> Optional[FunctionType]:
        return self._function_type

    @function_type.setter
    def function_type(self, t: FunctionType):
        self._function_type = t

    @property
    def is_constructor(self) -> bool:
        """
        bool: True if the function is the constructor
        """
        return self._function_type == FunctionType.CONSTRUCTOR

    @property
    def is_constructor_variables(self) -> bool:
        """
        bool: True if the function is the constructor of the variables
        Slither has inbuilt functions to hold the state variables initialization
        """
        return self._function_type in [
            FunctionType.CONSTRUCTOR_VARIABLES,
            FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES,
        ]

    @property
    def is_fallback(self) -> bool:
        """
            Determine if the function is the fallback function for the contract
        Returns
            (bool)
        """
        return self._function_type == FunctionType.FALLBACK

    @property
    def is_receive(self) -> bool:
        """
            Determine if the function is the receive function for the contract
        Returns
            (bool)
        """
        return self._function_type == FunctionType.RECEIVE

    @property
    def payable(self) -> bool:
        """
        bool: True if the function is payable
        """
        return self._payable

    @payable.setter
    def payable(self, p: bool):
        self._payable = p

    @property
    def visibility(self) -> str:
        """
        str: Function visibility
        """
        assert self._visibility is not None
        return self._visibility

    @visibility.setter
    def visibility(self, v: str):
        self._visibility = v

    def set_visibility(self, v: str):
        self._visibility = v
    
    @property
    def view(self) -> bool:
        """
        bool: True if the function is declared as view
        """
        return self._view

    @view.setter
    def view(self, v: bool):
        self._view = v

    @property
    def pure(self) -> bool:
        """
        bool: True if the function is declared as pure
        """
        return self._pure

    @pure.setter
    def pure(self, p: bool):
        self._pure = p

    @property
    def signature(self) -> Tuple[str, List[str], List[str]]:
        """
        (str, list(str), list(str)): Function signature as
        (name, list parameters type, list return values type)
        """
        if self._signature is None:
            signature = (
                self.name,
                [str(x.type) for x in self.parameters],
                [str(x.type) for x in self.returns],
            )
            self._signature = signature
        return self._signature
    
    @property
    def parameters(self) -> List["LocalVariable"]:
        """
        list(LocalVariable): List of the parameters
        """
        return list(self._parameters)
    @property
    def internal_calls(self) -> List["InternalCallType"]:
        """
        list(Function or SolidityFunction): List of function calls (that does not create a transaction)
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
    def all_internal_calls(self) -> List["InternalCallType"]:
        """recursive version of internal_calls"""
        if self._all_internals_calls is None:
            self._all_internals_calls = self._explore_functions(lambda x: x.internal_calls)
        return self._all_internals_calls

    def all_low_level_calls(self) -> List["LowLevelCallType"]:
        """recursive version of low_level calls"""
        if self._all_low_level_calls is None:
            self._all_low_level_calls = self._explore_functions(lambda x: x.low_level_calls)
        return self._all_low_level_calls

    def all_high_level_calls(self) -> List["HighLevelCallType"]:
        """recursive version of high_level calls"""
        if self._all_high_level_calls is None:
            self._all_high_level_calls = self._explore_functions(lambda x: x.high_level_calls)
        return self._all_high_level_calls

    def all_library_calls(self) -> List["LibraryCallType"]:
        """recursive version of library calls"""
        if self._all_library_calls is None:
            self._all_library_calls = self._explore_functions(lambda x: x.library_calls)
        return self._all_library_calls

    def all_solidity_calls(self) -> List[SolidityFunction]:
        """recursive version of solidity calls"""
        if self._all_solidity_calls is None:
            self._all_solidity_calls = self._explore_functions(lambda x: x.solidity_calls)
        return self._all_solidity_calls

    @property
    def modifiers(self) -> List[Union["Contract", "Function"]]:
        """
        list(Modifier): List of the modifiers
        Can be contract for constructor's calls

        """
        return [c.modifier for c in self._modifiers]
    def all_internal_calls(self) -> List["InternalCallType"]:
        """recursive version of internal_calls"""
        if self._all_internals_calls is None:
            self._all_internals_calls = self._explore_functions(lambda x: x.internal_calls)
        return self._all_internals_calls
    
    def _explore_functions(self, f_new_values: Callable[["Function"], List]):
        values = f_new_values(self)
        explored = [self]
        to_explore = [
            c for c in self.internal_calls if isinstance(c, Function) and c not in explored
        ]
        to_explore += [
            c for (_, c) in self.library_calls if isinstance(c, Function) and c not in explored
        ]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)

            values += f_new_values(f)

            to_explore += [
                c
                for c in f.internal_calls
                if isinstance(c, Function) and c not in explored and c not in to_explore
            ]
            to_explore += [
                c
                for (_, c) in f.library_calls
                if isinstance(c, Function) and c not in explored and c not in to_explore
            ]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(values))

    def add_parameters(self, p: "LocalVariable"):
        self._parameters.append(p)

    def parameters_src(self) -> SourceMapping:
        return self._parameters_src
    
    @property
    def return_type(self) -> Optional[List[Type]]:
        """
        Return the list of return type
        If no return, return None
        """
        returns = self.returns
        if returns:
            return [r.type for r in returns]
        return None

    def returns_src(self) -> SourceMapping:
        return self._returns_src

    @property
    def returns(self) -> List["LocalVariable"]:
        """
        list(LocalVariable): List of the return variables
        """
        return list(self._returns)

    def add_return(self, r: "LocalVariable"):
        self._returns.append(r)
    
    @property
    def full_name(self) -> str:
        """
        str: func_name(type1,type2)
        Return the function signature without the return values
        The difference between this function and solidity_function is that full_name does not translate the underlying
        type (ex: structure, contract to address, ...)
        """
        if self._full_name is None:
            name, parameters, _ = self.signature
            full_name = ".".join(self._internal_scope + [name]) + "(" + ",".join(parameters) + ")"
            self._full_name = full_name
        return self._full_name

    @property
    @abstractmethod
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        return ""

    @property
    def variables(self) -> List[LocalVariable]:
        """
        Return all local variables
        Include paramters and return values
        """
        return list(self._variables.values())

    @property
    def local_variables(self) -> List[LocalVariable]:
        """
        Return all local variables (dont include paramters and return values)
        """
        return list(set(self.variables) - set(self.returns) - set(self.parameters))

    @property
    def variables_as_dict(self) -> Dict[str, LocalVariable]:
        return self._variables

    @property
    def variables_read(self) -> List["Variable"]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def variables_written(self) -> List["Variable"]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_read(self) -> List["StateVariable"]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def solidity_variables_read(self) -> List["SolidityVariable"]:
        """
        list(SolidityVariable): Solidity variables read
        """
        return list(self._solidity_vars_read)

    @property
    def state_variables_written(self) -> List["StateVariable"]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def variables_read_or_written(self) -> List["Variable"]:
        """
        list(Variable): Variables read or written (local/state/solidity)
        """
        return list(self._vars_read_or_written)

    @property
    def variables_read_as_expression(self) -> List["Expression"]:
        return self._expression_vars_read

    @property
    def variables_written_as_expression(self) -> List["Expression"]:
        return self._expression_vars_written
    
    def new_node(
        self, node_type: "NodeType", src: Union[str, Dict], scope: Union[Scope, "Function"]
    ) -> "Node":
        from mythril.ast.core.cfg.node import Node

        node = Node(node_type, self._counter_nodes, scope, self.file_scope)
        node.set_offset(src, self.compilation_unit)
        self._counter_nodes += 1
        node.set_function(self)
        self._nodes.append(node)

        return node
    
    def generate_astir_and_analyze(self):
        for node in self.nodes:
            node.astir_generation()
        # tim hieu cho nay
        self._analyze_read_write()
        # print("self.state_variables_written",  self.state_variables_written)
        self._analyze_calls()
    def _analyze_read_write(self):
        """Compute variables read/written/..."""
        write_var = [x.variables_written_as_expression for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_written = write_var
        write_var = [x.variables_written for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._vars_written = write_var

        read_var = [x.variables_read_as_expression for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [
            next(obj)
            for i, obj in groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_read = read_var

        read_var = [x.variables_read for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [
            next(obj)
            for i, obj in groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._vars_read = read_var

        self._state_vars_written = [
            x for x in self.variables_written if isinstance(x, StateVariable)
        ]
        self._state_vars_read = [x for x in self.variables_read if isinstance(x, StateVariable)]
        self._solidity_vars_read = [
            x for x in self.variables_read if isinstance(x, SolidityVariable)
        ]
        self._vars_read_or_written = self._vars_written + self._vars_read

        astir_variables = [x.astir_variables for x in self.nodes]
        astir_variables = [x for x in astir_variables if x]
        self._astir_variables = [item for sublist in astir_variables for item in sublist]

    def _analyze_calls(self):
        calls = [x.calls_as_expression for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        self._expression_calls = list(set(calls))

        internal_calls = [x.internal_calls for x in self.nodes]
        internal_calls = [x for x in internal_calls if x]
        internal_calls = [item for sublist in internal_calls for item in sublist]
        self._internal_calls = list(set(internal_calls))

        self._solidity_calls = [c for c in internal_calls if isinstance(c, SolidityFunction)]

        low_level_calls = [x.low_level_calls for x in self.nodes]
        low_level_calls = [x for x in low_level_calls if x]
        low_level_calls = [item for sublist in low_level_calls for item in sublist]
        self._low_level_calls = list(set(low_level_calls))

        high_level_calls = [x.high_level_calls for x in self.nodes]
        high_level_calls = [x for x in high_level_calls if x]
        high_level_calls = [item for sublist in high_level_calls for item in sublist]
        self._high_level_calls = list(set(high_level_calls))

        library_calls = [x.library_calls for x in self.nodes]
        library_calls = [x for x in library_calls if x]
        library_calls = [item for sublist in library_calls for item in sublist]
        self._library_calls = list(set(library_calls))

        external_calls_as_expressions = [x.external_calls_as_expressions for x in self.nodes]
        external_calls_as_expressions = [x for x in external_calls_as_expressions if x]
        external_calls_as_expressions = [
            item for sublist in external_calls_as_expressions for item in sublist
        ]
        self._external_calls_as_expressions = list(set(external_calls_as_expressions))

    def __str__(self):
        return self.name
