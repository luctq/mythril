from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union, Set

from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.declarations.function import Function, FunctionLanguage
from mythril.ast.core.declarations.modifier import Modifier
if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.core.scope.scope import FileScope
    from mythril.ast.core.variables.state_variable import StateVariable
    from mythril.ast.utils.type_helpers import InternalCallType
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
        self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        # self._linearizedBaseContracts: List[int] = []
        # self._custom_errors: Dict[str, "CustomErrorContract"] = {}
        self._all_functions_called: Optional[List["InternalCallType"]] = None

        self._kind: Optional[str] = None
        self._is_interface: bool = False
        self._is_library: bool = False
        self.is_top_level = False
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
    def modifiers(self) -> List["Modifier"]:
        """
        list(Modifier): List of the modifiers
        """
        return list(self._modifiers.values())

    @property
    def is_library(self) -> bool:
        return self._is_library

    @is_library.setter
    def is_library(self, is_library: bool):
        self._is_library = is_library

    @property
    def variables(self) -> List["StateVariable"]:
        """
        Returns all the accessible variables (do not include private variable from inherited contract)

        list(StateVariable): List of the state variables. Alias to self.state_variables.
        """
        return list(self.state_variables)
    
    @property
    def variables_as_dict(self) -> Dict[str, "StateVariable"]:
        return self._variables
    
    @property
    def state_variables(self) -> List["StateVariable"]:
        """
        Returns all the accessible variables (do not include private variable from inherited contract).
        Use state_variables_ordered for all the variables following the storage order

        list(StateVariable): List of the state variables.
        """
        return list(self._variables.values())
    
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
    
    @property
    def functions_and_modifiers_declared(self) -> List["Function"]:
        """
        list(Function|Modifier): List of the functions and modifiers defined within the contract (not inherited)
        """
        return self.functions_declared #+ self.modifiers_declared
    
    @property
    def all_functions_called(self) -> List["InternalCallType"]:
        """
        list(Function): List of functions reachable from the contract
        Includes super, and private/internal functions not shadowed
        """
        if self._all_functions_called is None:
            all_functions = [f for f in self.functions + self.modifiers if not f.is_shadowed]  # type: ignore
            all_callss = [f.all_internal_calls() for f in all_functions] + [list(all_functions)]
            all_calls = [item for sublist in all_callss for item in sublist]
            all_calls = list(set(all_calls))

            all_constructors = [c.constructor for c in self.inheritance if c.constructor]
            all_constructors = list(set(all_constructors))

            set_all_calls = set(all_calls + list(all_constructors))

            self._all_functions_called = [c for c in set_all_calls if isinstance(c, Function)]
        return self._all_functions_called

    @property
    def functions_entry_points(self) -> List["FunctionContract"]:
        """
        list(Functions): List of public and external functions
        """
        return [
            f
            for f in self.functions
            if f.visibility in ["public", "external"] and not f.is_shadowed or f.is_fallback
        ]

    def is_from_dependency(self) -> bool:
        return self.compilation_unit.core.crytic_compile.is_dependency(
            self.source_mapping.filename.absolute
        )
    def is_signature_only(self) -> bool:
        """Detect if the contract has only abstract functions

        Returns:
            bool: true if the function are abstract functions
        """
        return all((not f.is_implemented) for f in self.functions)

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

    def __str__(self):
        return self.name
