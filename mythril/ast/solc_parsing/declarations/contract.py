from typing import List, Dict, Callable, TYPE_CHECKING, Union
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.solc_parsing.declarations.function import FunctionSolc
from mythril.ast.solc_parsing.declarations.modifier import ModifierSolc
from mythril.ast.solc_parsing.exceptions import ParsingError
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.solc_parsing.variables.state_variable import StateVariableSolc
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
        # self._parse_base_contract_info()

        # trufle does some re-mapping of id
        # if "baseContracts" in self._data:
        #     for elem in self._data["baseContracts"]:
        #         if elem["nodeType"] == "InheritanceSpecifier":
        #             self._remapping[elem["baseName"]["referencedDeclaration"]] = elem["baseName"][
        #                 "name"
        #             ]
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
            pass

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
    