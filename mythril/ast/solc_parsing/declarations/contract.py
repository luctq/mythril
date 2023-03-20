from typing import List, Dict, Callable, TYPE_CHECKING, Union, Set
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.declarations.function import Function
from mythril.ast.solc_parsing.declarations.function import FunctionSolc
from mythril.ast.solc_parsing.declarations.modifier import ModifierSolc
from mythril.ast.solc_parsing.exceptions import ParsingError, VariableNotFound
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.solc_parsing.variables.state_variable import StateVariableSolc
from mythril.ast.core.declarations.modifier import Modifier
if TYPE_CHECKING:
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
class ContractSolc(CallerContextExpression):
    def __init__(self, static_parser: "StaticCompilationUnitSolc", contract: Contract, data):
        self._contract = contract
        self._static_parser = static_parser
        self._data = data


        self._functionsNotParsed: List[Dict] = []
        self._modifiersNotParsed: List[Dict] = []
        self._functions_no_params: List[FunctionSolc] = []
        self._modifiers_no_params: List[ModifierSolc] = []
        self._eventsNotParsed: List[Dict] = []
        self._variablesNotParsed: List[Dict] = []
        self._enumsNotParsed: List[Dict] = []
        self._structuresNotParsed: List[Dict] = []
        self._usingForNotParsed: List[Dict] = []
        self._customErrorNotParsed: List[Dict] = []
        
        self._functions_parser: List[FunctionSolc] = []
        self._modifiers_parser: List[ModifierSolc] = []

        self._is_analyzed: bool = False

        # use to remap inheritance id
        self._remapping: Dict[str, str] = {}
        self.baseContracts: List[str] = []
        self.baseConstructorContractsCalled: List[str] = []
        self._linearized_base_contracts: List[int]

        self._variables_parser: List[StateVariableSolc] = []
        
        if self.is_compact_ast:
            self._contract.name = self._data["name"]
            # self._handle_comment(self._data)
        else:
            self._contract.name = self._data["attributes"][self.get_key()]
            # self._handle_comment(self._data["attributes"])
        self._contract.id = self._data["id"]

        self._parse_contract_info()
        self._parse_contract_items()

    @property
    def is_analyzed(self) -> bool:
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed: bool):
        self._is_analyzed = is_analyzed
    
    @property
    def underlying_contract(self) -> Contract:
        return self._contract

    @property
    def linearized_base_contracts(self) -> List[int]:
        return self._linearized_base_contracts

    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self._contract.compilation_unit

    @property
    def static_parser(self) -> "StaticCompilationUnitSolc":
        return self._static_parser

    @property
    def functions_parser(self) -> List["FunctionSolc"]:
        return self._functions_parser

    @property
    def modifiers_parser(self) -> List["ModifierSolc"]:
        return self._modifiers_parser

    @property
    def structures_not_parsed(self) -> List[Dict]:
        return self._structuresNotParsed

    @property
    def enums_not_parsed(self) -> List[Dict]:
        return self._enumsNotParsed

    @property
    def is_compact_ast(self) -> bool:
        return self._static_parser.is_compact_ast

    def get_key(self) -> str:
        return self._static_parser.get_key()

    def get_children(self, key="nodes") -> str:
        if self.is_compact_ast:
            return key
        return "children"
    
    def _parse_contract_info(self):
        if self.is_compact_ast:
            attributes = self._data
        else:
            attributes = self._data["attributes"]
        self._contract.is_interface = False
        if "contractKind" in attributes:
            if attributes["contractKind"] == "interface":
                self._contract.is_interface = True
            elif attributes["contractKind"] == "library":
                self._contract.is_library = True
            self._contract.contract_kind = attributes["contractKind"]
        self._linearized_base_contracts = attributes["linearizedBaseContracts"]
        
        # Parse base contract information
        self._parse_base_contract_info()

        # trufle does some re-mapping of id
        if "baseContracts" in self._data:
            for elem in self._data["baseContracts"]:
                if elem["nodeType"] == "InheritanceSpecifier":
                    self._remapping[elem["baseName"]["referencedDeclaration"]] = elem["baseName"][
                        "name"
                    ]
    def _parse_base_contract_info(self):  # pylint: disable=too-many-branches
        # Parse base contracts (immediate, non-linearized)
        if self.is_compact_ast:
            # Parse base contracts + constructors in compact-ast
            if "baseContracts" in self._data:
                for base_contract in self._data["baseContracts"]:
                    if base_contract["nodeType"] != "InheritanceSpecifier":
                        continue
                    if (
                        "baseName" not in base_contract
                        or "referencedDeclaration" not in base_contract["baseName"]
                    ):
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract["baseName"]["referencedDeclaration"]
                    self.baseContracts.append(referencedDeclaration)

                    # If we have defined arguments in our arguments object, this is a constructor invocation.
                    # (note: 'arguments' can be [], which is not the same as None. [] implies a constructor was
                    #  called with no arguments, while None implies no constructor was called).
                    if "arguments" in base_contract and base_contract["arguments"] is not None:
                        self.baseConstructorContractsCalled.append(referencedDeclaration)
        else:
            # Parse base contracts + constructors in legacy-ast
            if "children" in self._data:
                for base_contract in self._data["children"]:
                    if base_contract["name"] != "InheritanceSpecifier":
                        continue
                    if "children" not in base_contract or len(base_contract["children"]) == 0:
                        continue
                    # Obtain all items for this base contract specification (base contract, followed by arguments)
                    base_contract_items = base_contract["children"]
                    if (
                        "name" not in base_contract_items[0]
                        or base_contract_items[0]["name"] != "UserDefinedTypeName"
                    ):
                        continue
                    if (
                        "attributes" not in base_contract_items[0]
                        or "referencedDeclaration" not in base_contract_items[0]["attributes"]
                    ):
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract_items[0]["attributes"][
                        "referencedDeclaration"
                    ]
                    self.baseContracts.append(referencedDeclaration)

                    # If we have an 'attributes'->'arguments' which is None, this is not a constructor call.
                    if (
                        "attributes" not in base_contract
                        or "arguments" not in base_contract["attributes"]
                        or base_contract["attributes"]["arguments"] is not None
                    ):
                        self.baseConstructorContractsCalled.append(referencedDeclaration)
    def _parse_contract_items(self):
        if not self.get_children() in self._data:  # empty contract
            return
        for item in self._data[self.get_children()]:
            if item[self.get_key()] == "FunctionDefinition":
                self._functionsNotParsed.append(item)
            elif item[self.get_key()] == "EventDefinition":
                self._eventsNotParsed.append(item)
            elif item[self.get_key()] == "InheritanceSpecifier":
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif item[self.get_key()] == "VariableDeclaration":
                self._variablesNotParsed.append(item)
            elif item[self.get_key()] == "EnumDefinition":
                self._enumsNotParsed.append(item)
            elif item[self.get_key()] == "ModifierDefinition":
                self._modifiersNotParsed.append(item)
            elif item[self.get_key()] == "StructDefinition":
                self._structuresNotParsed.append(item)
            elif item[self.get_key()] == "UsingForDirective":
                self._usingForNotParsed.append(item)
            elif item[self.get_key()] == "ErrorDefinition":
                self._customErrorNotParsed.append(item)
            # elif item[self.get_key()] == "UserDefinedValueTypeDefinition":
                # self._parse_type_alias(item)
                pass
            else:
                raise ParsingError("Unknown contract item: " + item[self.get_key()])
        return
    
    def parse_state_variables(self):
        for father in self._contract.inheritance_reverse:
            self._contract.variables_as_dict.update(
                {
                    name: v
                    for name, v in father.variables_as_dict.items()
                    if v.visibility != "private"
                }
            )
            self._contract.add_variables_ordered(
                [
                    var
                    for var in father.state_variables_ordered
                    if var not in self._contract.state_variables_ordered
                ]
            )
        for varNotParsed in self._variablesNotParsed:
            var = StateVariable()
            var.set_offset(varNotParsed["src"], self._contract.compilation_unit)
            var.set_contract(self._contract)

            var_parser = StateVariableSolc(var, varNotParsed)
            self._variables_parser.append(var_parser)

            self._contract.variables_as_dict[var.name] = var
            self._contract.add_variables_ordered([var])

    def parse_functions(self):
        for function in self._functionsNotParsed:
            self._parse_function(function)
        self._functionsNotParsed = None

    def _parse_function(self, function_data):
        func = FunctionContract(self._contract.compilation_unit)
        func.set_offset(function_data["src"], self._contract.compilation_unit)
        func.set_contract(self._contract)
        func.set_contract_declarer(self._contract)
        func_parser = FunctionSolc(func, function_data, self, self._static_parser)
        self._contract.compilation_unit.add_function(func)
        self._functions_no_params.append(func_parser)
        self._functions_parser.append(func_parser)
        self._static_parser.add_function_or_modifier_parser(func_parser)

    def analyze_params_functions(self):
        try:
            elements_no_params = self._functions_no_params
            getter = lambda c: c.functions_parser
            getter_available = lambda c: c.functions_declared
            Cls = FunctionContract
            Cls_parser = FunctionSolc
            functions = self._analyze_params_elements(
                elements_no_params,
                getter,
                getter_available,
                Cls,
                Cls_parser,
                self._functions_parser,
            )
            self._contract.set_functions(functions)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing params {e}")
        self._functions_no_params = []
    
    def analyze_content_functions(self):
        try:
            for function_parser in self._functions_parser:
                function_parser.analyze_content()
        except (VariableNotFound, KeyError, ParsingError) as e:
            self.log_incorrect_parsing(f"Missing function {e}")
    
    def analyze_state_variables(self):
        try:
            for var_parser in self._variables_parser:
                var_parser.analyze(self)
            return
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing state variable {e}")

    def _analyze_params_elements(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        elements_no_params: List[FunctionSolc],
        getter: Callable[["ContractSolc"], List[FunctionSolc]],
        getter_available: Callable[[Contract], List[FunctionContract]],
        Cls: Callable,
        Cls_parser: Callable,
        parser: List[FunctionSolc],
    ) -> Dict[str, Union[FunctionContract, Modifier]]:
        
        all_elements = {}

        try:

            # If there is a constructor in the functions
            # We remove the previous constructor
            # As only one constructor is present per contracts
            #
            # Note: contract.all_functions_called returns the constructors of the base contracts
            has_constructor = False
            for element_parser in elements_no_params:
                # cho nay de parse cacs bien cho function
                element_parser.analyze_params()
                if element_parser.underlying_function.is_constructor:
                    has_constructor = True

           
            for element_parser in elements_no_params:
                all_elements[
                    element_parser.underlying_function.canonical_name
                ] = element_parser.underlying_function

        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing params {e}")
        return all_elements
    
    def log_incorrect_parsing(self, error: str) -> None:
        pass
        # if self._contract.compilation_unit.core.disallow_partial:
        #     raise ParsingError(error)
        # self._contract.is_incorrectly_constructed = True
   