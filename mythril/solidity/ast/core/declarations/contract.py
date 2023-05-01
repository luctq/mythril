from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union, Set

from mythril.solidity.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.solidity.ast.core.declarations.function_contract import FunctionContract
from mythril.solidity.ast.core.declarations.function import Function, FunctionLanguage, FunctionType
from mythril.solidity.ast.core.declarations.modifier import Modifier
from mythril.solidity.ast.core.declarations.structure_contract import StructureContract
from mythril.solidity.ast.core.declarations.enum_contract import EnumContract
from mythril.solidity.ast.core.declarations.event import Event
from mythril.solidity.ast.core.declarations.custom_error_contract import CustomErrorContract
from mythril.solidity.ast.core.variables.variable import Variable
from mythril.solidity.ast.core.cfg.scope import Scope

if TYPE_CHECKING:
    from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.solidity.ast.core.scope.scope import FileScope
    from mythril.solidity.ast.core.variables.state_variable import StateVariable
    from mythril.solidity.ast.utils.type_helpers import InternalCallType
class Contract(SourceMapping):
    def __init__(self, compilation_unit: "StaticCompilationUnit", scope: "FileScope"):
        super().__init__()
        self._name: Optional[str] = None
        self._id: Optional[int] = None
        self._inheritance: List["Contract"] = []  # all contract inherited, c3 linearization
        self._immediate_inheritance: List["Contract"] = []  # immediate inheritance  

        # Constructors called on contract's definition
        # contract B is A(1) { ..
        self._explicit_base_constructor_calls: List["Contract"] = []
        self._enums: Dict[str, "EnumContract"] = {}
        self._structures: Dict[str, "StructureContract"] = {}
        self._events: Dict[str, "Event"] = {}
        self._variables: Dict[str, "StateVariable"] = {}
        self._variables_ordered: List["StateVariable"] = []
        self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        # self._linearizedBaseContracts: List[int] = []
        self._custom_errors: Dict[str, "CustomErrorContract"] = {}
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
    def constructor(self) -> Optional["Function"]:
        """
        Return the contract's immediate constructor.
        If there is no immediate constructor, returns the first constructor
        executed, following the c3 linearization
        Return None if there is no constructor.
        """
        cst = self.constructors_declared
        if cst:
            return cst
        for inherited_contract in self.inheritance:
            cst = inherited_contract.constructors_declared
            if cst:
                return cst
        return None

    @property
    def constructors_declared(self) -> Optional["Function"]:
        return next(
            (
                func
                for func in self.functions
                if func.is_constructor and func.contract_declarer == self
            ),
            None,
        )

    @property
    def constructors(self) -> List["Function"]:
        """
        Return the list of constructors (including inherited)
        """
        return [func for func in self.functions if func.is_constructor]

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
    def modifiers_inherited(self) -> List["Modifier"]:
        """
        list(Modifier): List of the inherited modifiers
        """
        return [m for m in self.modifiers if m.contract_declarer != self]

    @property
    def modifiers_declared(self) -> List["Modifier"]:
        """
        list(Modifier): List of the modifiers defined within the contract (not inherited)
        """
        return [m for m in self.modifiers if m.contract_declarer == self]
    
    def available_modifiers_as_dict(self) -> Dict[str, "Modifier"]:
        return {m.full_name: m for m in self._modifiers.values() if not m.is_shadowed}

    def set_modifiers(self, modifiers: Dict[str, "Modifier"]):
        """
        Set the modifiers

        :param modifiers:  dict full_name -> modifier
        :return:
        """
        self._modifiers = modifiers

    @property
    def is_library(self) -> bool:
        return self._is_library

    @is_library.setter
    def is_library(self, is_library: bool):
        self._is_library = is_library


    @property
    def structures(self) -> List["StructureContract"]:
        """
        list(Structure): List of the structures
        """
        return list(self._structures.values())

    @property
    def structures_inherited(self) -> List["StructureContract"]:
        """
        list(Structure): List of the inherited structures
        """
        return [s for s in self.structures if s.contract != self]

    @property
    def structures_declared(self) -> List["StructureContract"]:
        """
        list(Structues): List of the structures declared within the contract (not inherited)
        """
        return [s for s in self.structures if s.contract == self]

    @property
    def structures_as_dict(self) -> Dict[str, "StructureContract"]:
        return self._structures
    
    @property
    def custom_errors(self) -> List["CustomErrorContract"]:
        """
        list(CustomErrorContract): List of the contract's custom errors
        """
        return list(self._custom_errors.values())

    @property
    def custom_errors_as_dict(self) -> Dict[str, "CustomErrorContract"]:
        return self._custom_errors

    @property
    def enums(self) -> List["EnumContract"]:
        return list(self._enums.values())

    @property
    def enums_inherited(self) -> List["EnumContract"]:
        """
        list(Enum): List of the inherited enums
        """
        return [e for e in self.enums if e.contract != self]

    @property
    def enums_declared(self) -> List["EnumContract"]:
        """
        list(Enum): List of the enums declared within the contract (not inherited)
        """
        return [e for e in self.enums if e.contract == self]

    @property
    def enums_as_dict(self) -> Dict[str, "EnumContract"]:
        return self._enums
    
    @property
    def events(self) -> List["Event"]:
        """
        list(Event): List of the events
        """
        return list(self._events.values())

    @property
    def events_inherited(self) -> List["Event"]:
        """
        list(Event): List of the inherited events
        """
        return [e for e in self.events if e.contract != self]

    @property
    def events_declared(self) -> List["Event"]:
        """
        list(Event): List of the events declared within the contract (not inherited)
        """
        return [e for e in self.events if e.contract == self]

    @property
    def events_as_dict(self) -> Dict[str, "Event"]:
        return self._events

    @property
    def custom_errors(self) -> List["CustomErrorContract"]:
        """
        list(CustomErrorContract): List of the contract's custom errors
        """
        return list(self._custom_errors.values())

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

    def set_inheritance(
        self,
        inheritance: List["Contract"],
        immediate_inheritance: List["Contract"],
        called_base_constructor_contracts: List["Contract"],
    ):
        self._inheritance = inheritance
        self._immediate_inheritance = immediate_inheritance
        self._explicit_base_constructor_calls = called_base_constructor_contracts

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
    
    @property
    def state_variables_ordered(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables by order of declaration.
        """
        return list(self._variables_ordered)
    
    def add_variables_ordered(self, new_vars: List["StateVariable"]):
        self._variables_ordered += new_vars

    @property
    def state_variables_declared(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables declared within the contract (not inherited)
        """
        return [s for s in self.state_variables if s.contract == self]

    def add_constructor_variables(self):
        from mythril.solidity.ast.core.declarations.function_contract import FunctionContract

        if self.state_variables:
            for (idx, variable_candidate) in enumerate(self.state_variables):
                if variable_candidate.expression and not variable_candidate.is_constant:

                    constructor_variable = FunctionContract(self.compilation_unit)
                    constructor_variable.set_function_type(FunctionType.CONSTRUCTOR_VARIABLES)
                    constructor_variable.set_contract(self)
                    constructor_variable.set_contract_declarer(self)
                    constructor_variable.set_visibility("internal")
                    # For now, source mapping of the constructor variable is the whole contract
                    # Could be improved with a targeted source mapping
                    constructor_variable.set_offset(self.source_mapping, self.compilation_unit)
                    self._functions[constructor_variable.canonical_name] = constructor_variable

                    prev_node = self._create_node(
                        constructor_variable, 0, variable_candidate, constructor_variable
                    )
                    variable_candidate.node_initialization = prev_node
                    counter = 1
                    for v in self.state_variables[idx + 1 :]:
                        if v.expression and not v.is_constant:
                            next_node = self._create_node(
                                constructor_variable, counter, v, prev_node.scope
                            )
                            v.node_initialization = next_node
                            prev_node.add_son(next_node)
                            next_node.add_father(prev_node)
                            prev_node = next_node
                            counter += 1
                    break

            for (idx, variable_candidate) in enumerate(self.state_variables):
                if variable_candidate.expression and variable_candidate.is_constant:

                    constructor_variable = FunctionContract(self.compilation_unit)
                    constructor_variable.set_function_type(
                        FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES
                    )
                    constructor_variable.set_contract(self)
                    constructor_variable.set_contract_declarer(self)
                    constructor_variable.set_visibility("internal")
                    # For now, source mapping of the constructor variable is the whole contract
                    # Could be improved with a targeted source mapping
                    constructor_variable.set_offset(self.source_mapping, self.compilation_unit)
                    self._functions[constructor_variable.canonical_name] = constructor_variable

                    prev_node = self._create_node(
                        constructor_variable, 0, variable_candidate, constructor_variable
                    )
                    variable_candidate.node_initialization = prev_node
                    counter = 1
                    for v in self.state_variables[idx + 1 :]:
                        if v.expression and v.is_constant:
                            next_node = self._create_node(
                                constructor_variable, counter, v, prev_node.scope
                            )
                            v.node_initialization = next_node
                            prev_node.add_son(next_node)
                            next_node.add_father(prev_node)
                            prev_node = next_node
                            counter += 1

                    break

    def _create_node(
        self, func: Function, counter: int, variable: "Variable", scope: Union[Scope, Function]
    ):
        from mythril.solidity.ast.core.cfg.node import Node, NodeType
        from mythril.solidity.ast.core.expressions import (
            AssignmentOperationType,
            AssignmentOperation,
            Identifier,
        )

        # Function uses to create node for state variable declaration statements
        node = Node(NodeType.OTHER_ENTRYPOINT, counter, scope, func.file_scope)
        node.set_offset(variable.source_mapping, self.compilation_unit)
        node.set_function(func)
        func.add_node(node)
        assert variable.expression
        expression = AssignmentOperation(
            Identifier(variable),
            variable.expression,
            AssignmentOperationType.ASSIGN,
            variable.type,
        )

        expression.set_offset(variable.source_mapping, self.compilation_unit)
        node.add_expression(expression)
        return node
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
