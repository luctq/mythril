from abc import abstractmethod, ABCMeta
from typing import Dict, TYPE_CHECKING, List, Optional, Set, Union, Callable, Tuple
from enum import Enum

from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.core.scope.scope import FileScope
from mythril.ast.core.cfg.scope import Scope
if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.cfg.node import Node, NodeType
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

        self._variables: Dict[str, "LocalVariable"] = {}
        self._full_name: Optional[str] = None
        self._signature: Optional[Tuple[str, List[str], List[str]]] = None
        self._solidity_signature: Optional[str] = None
        self._signature_str: Optional[str] = None
        self._canonical_name: Optional[str] = None
        self._is_protected: Optional[bool] = None

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
            return "slitherConstructorVariables"
        if self._function_type == FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES:
            return "slitherConstructorConstantVariables"
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
