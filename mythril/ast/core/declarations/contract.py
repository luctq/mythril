from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union, Set

from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.declarations.function import Function, FunctionLanguage
if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.scope.scope import FileScope
    from mythril.ast.core.variables.state_variable import StateVariable
class Contract(SourceMapping):
    def __init__(self, compilation_unit: "StaticCompilationUnit", scope: "FileScope"):
        super().__init__()
        self._name: Optional[str] = None
        self._id: Optional[int] = None
        self._inheritance: List["Contract"] = []  

        # self._explicit_base_constructor_calls: List["Contract"] = []
        # self._enums: Dict[str, "EnumContract"] = {}
        # self._structures: Dict[str, "StructureContract"] = {}
        # self._events: Dict[str, "Event"] = {}
        self._variables: Dict[str, "StateVariable"] = {}
        self._variables_ordered: List["StateVariable"] = []
        # self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        # self._linearizedBaseContracts: List[int] = []
        # self._custom_errors: Dict[str, "CustomErrorContract"] = {}

        self._kind: Optional[str] = None
        self._is_interface: bool = False
        self._is_library: bool = False
        self.compilation_unit: "StaticCompilationUnit" = compilation_unit
        self.file_scope: "FileScope" = scope
    @property
    def name(self) -> str:
        """str: Name of the contract."""
        assert self._name
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def id(self) -> int:
        """Unique id."""
        assert self._id
        return self._id

    @id.setter
    def id(self, new_id):
        """Unique id."""
        self._id = new_id

    @property
    def inheritance(self) -> List["Contract"]:
        """
        list(Contract): Inheritance list. Order: the first elem is the first father to be executed
        """
        return list(self._inheritance)
    
    @property
    def inheritance_reverse(self) -> List["Contract"]:
        """
        list(Contract): Inheritance list. Order: the last elem is the first father to be executed
        """
        return list(reversed(self._inheritance))

    @property
    def contract_kind(self) -> Optional[str]:
        """
        contract_kind can be None if the legacy ast format is used
        :return:
        """
        return self._kind

    @contract_kind.setter
    def contract_kind(self, kind):
        self._kind = kind

    @property
    def is_interface(self) -> bool:
        return self._is_interface

    @is_interface.setter
    def is_interface(self, is_interface: bool):
        self._is_interface = is_interface

    @property
    def is_library(self) -> bool:
        return self._is_library

    @is_library.setter
    def is_library(self, is_library: bool):
        self._is_library = is_library
    
    @property
    def variables_as_dict(self) -> Dict[str, "StateVariable"]:
        return self._variables
    
    @property
    def functions(self) -> List["FunctionContract"]:
        """
        list(Function): List of the functions
        """
        return list(self._functions.values())
    def set_functions(self, functions: Dict[str, "FunctionContract"]):
        """
        Set the functions

        :param functions:  dict full_name -> function
        :return:
        """
        self._functions = functions


    @property
    def functions_declared(self) -> List["FunctionContract"]:
        """
        list(Function): List of the functions defined within the contract (not inherited)
        """
        return [f for f in self.functions if f.contract_declarer == self]
    
    def add_variables_ordered(self, new_vars: List["StateVariable"]):
        self._variables_ordered += new_vars

    def available_elements_from_inheritances(
        self,
        elements: Dict[str, "Function"],
        getter_available: Callable[["Contract"], List["FunctionContract"]],
    ) -> Dict[str, "Function"]:
        """

        :param elements: dict(canonical_name -> elements)
        :param getter_available: fun x
        :return:
        """
        # keep track of the contracts visited
        # to prevent an ovveride due to multiple inheritance of the same contract
        # A is B, C, D is C, --> the second C was already seen
        inherited_elements: Dict[str, "FunctionContract"] = {}
        accessible_elements = {}
        contracts_visited = []
        for father in self.inheritance_reverse:
            functions: Dict[str, "FunctionContract"] = {
                v.full_name: v
                for v in getter_available(father)
                if v.contract not in contracts_visited
                and v.function_language
                != FunctionLanguage.Yul  # Yul functions are not propagated in the inheritance
            }
            contracts_visited.append(father)
            inherited_elements.update(functions)

        for element in inherited_elements.values():
            accessible_elements[element.full_name] = elements[element.canonical_name]

        return accessible_elements