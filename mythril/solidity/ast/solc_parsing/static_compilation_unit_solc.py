import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict

from mythril.solidity.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.solidity.ast.solc_parsing.declarations.contract import ContractSolc
from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.declarations.import_directive import Import
from mythril.solidity.ast.solc_parsing.declarations.structure_top_level import StructureTopLevelSolc
from mythril.solidity.ast.solc_parsing.declarations.custom_error import CustomErrorSolc
from mythril.solidity.ast.solc_parsing.declarations.function import FunctionSolc
from mythril.solidity.ast.core.declarations.pragma_directive import Pragma
from mythril.solidity.ast.core.scope.scope import FileScope

from mythril.exceptions import StaticException

def _handle_import_aliases(
    symbol_aliases: Dict, import_directive: Import, scope: FileScope
) -> None:
    """
    Handle the parsing of import aliases

    Args:
        symbol_aliases (Dict): json dict from solc
        import_directive (Import): current import directive
        scope (FileScope): current file scape

    Returns:

    """
    for symbol_alias in symbol_aliases:
        if "foreign" in symbol_alias and "local" in symbol_alias:
            if isinstance(symbol_alias["foreign"], dict) and "name" in symbol_alias["foreign"]:

                original_name = symbol_alias["foreign"]["name"]
                local_name = symbol_alias["local"]
                import_directive.renaming[local_name] = original_name
                # Assuming that two imports cannot collide in renaming
                scope.renaming[local_name] = original_name

            # This path should only be hit for the malformed AST of solc 0.5.12 where
            # the foreign identifier cannot be found but is required to resolve the alias.
            # see https://github.com/crytic/slither/issues/1319
            elif symbol_alias["local"]:
                raise StaticException(
                    "Cannot resolve local alias for import directive due to malformed AST. Please upgrade to solc 0.6.0 or higher."
                )

class StaticCompilationUnitSolc(CallerContextExpression):
    def __init__(self, compilation_unit: StaticCompilationUnit):
        super().__init__();
        self._contracts_by_id: Dict[int, ContractSolc] = {}
        self._parsed = False
        self._analyzed = False
        self._compilation_unit = compilation_unit

        self._underlying_contract_to_parser: Dict[Contract, ContractSolc] = {}
        self._structures_top_level_parser: List[StructureTopLevelSolc] = []
        self._custom_error_parser: List[CustomErrorSolc] = []
        # self._variables_top_level_parser: List[TopLevelVariableSolc] = []
        self._functions_top_level_parser: List[FunctionSolc] = []
        # self._using_for_top_level_parser: List[UsingForTopLevelSolc] = []

        self._is_compact_ast = False

        self._all_functions_and_modifier_parser: List[FunctionSolc] = []

        self._top_level_contracts_counter = 0

    @property
    def compilation_unit(self) -> StaticCompilationUnit:
        return self._compilation_unit

    @property
    def all_functions_and_modifiers_parser(self) -> List[FunctionSolc]:
        return self._all_functions_and_modifier_parser

    def add_function_or_modifier_parser(self, f: FunctionSolc):
        self._all_functions_and_modifier_parser.append(f)
    
    @property
    def underlying_contract_to_parser(self) -> Dict[Contract, ContractSolc]:
        return self._underlying_contract_to_parser

    @property
    def static_parser(self) -> "StaticCompilationUnitSolc":
        return self
    
    def get_key(self) -> str:
        if self._is_compact_ast:
            return "nodeType"
        return "name"
    
    def get_children(self) -> str:
        if self._is_compact_ast:
            return "nodes"
        return "children"

    @property
    def is_compact_ast(self) -> bool:
        return self._is_compact_ast

    
    def parse_top_level_of_ast(
        self, data_loaded: Dict, filename: str
    ):
        """This function parse data from bytecode ast json. 
        Each node will have its own task, so we will separate 
        and handle each task"""

        if "nodeType" in data_loaded:
            self._is_compact_ast = True

        if data_loaded[self.get_key()] == "SourceUnit":
           self._parse_source_unit(data_loaded, filename)
        else:
            # solc version is not supported
            return   
             
        if self.get_children() not in data_loaded:
            return
        
        scope = self.compilation_unit.get_scope(filename)
        # print("self.compilation_unit.get_scope(filename)", scope)
        # print("len(len(data_loaded[self.get_children()])", len(data_loaded[self.get_children()]))
        for top_level_data in data_loaded[self.get_children()]:
            if top_level_data[self.get_key()] == "ContractDefinition":
                contract = Contract(self._compilation_unit, scope)
                contract_parser = ContractSolc(self, contract, top_level_data)
                scope.contracts[contract.name] = contract
                if "src" in top_level_data:
                    contract.set_offset(top_level_data["src"], self._compilation_unit)

                self._underlying_contract_to_parser[contract] = contract_parser
            elif top_level_data[self.get_key()] == "PragmaDirective":
                pragma = Pragma(top_level_data["literals"], scope)
                scope.pragmas.add(pragma)
                pragma.set_offset(top_level_data["src"], self._compilation_unit)
                self._compilation_unit.pragma_directives.append(pragma)
            # handle later
            elif top_level_data[self.get_key()] == "UsingForDirective":
               print("UsingForDirective")
               pass

            elif top_level_data[self.get_key()] == "ImportDirective":
                import_directive = Import(
                    Path(
                        top_level_data["absolutePath"],
                    ),
                    scope,
                )
                scope.imports.add(import_directive)
                # TODO investigate unitAlias in version < 0.7 and legacy ast
                # import * as symbolName from "filename"; 
                if "unitAlias" in top_level_data:
                    import_directive.alias = top_level_data["unitAlias"]
                # import {symbol1 as alias, symbol2} from "filename"; 
                if "symbolAliases" in top_level_data:
                    symbol_aliases = top_level_data["symbolAliases"]
                    _handle_import_aliases(symbol_aliases, import_directive, scope)

                import_directive.set_offset(top_level_data["src"], self._compilation_unit)
                self._compilation_unit.imports.append(import_directive)

                # get_imported_scope = self.compilation_unit.get_scope(import_directive.filename)
                # scope.accessible_scopes.append(get_imported_scope)
                
            elif top_level_data[self.get_key()] == "StructDefinition":
               print("StructDefinition")
               pass 
            elif top_level_data[self.get_key()] == "EnumDefinition":
               print("EnumDefinition")
               pass
            elif top_level_data[self.get_key()] == "VariableDeclaration":
               pass
            elif top_level_data[self.get_key()] == "FunctionDefinition":
               print("FunctionDefinition")
               pass
            elif top_level_data[self.get_key()] == "ErrorDefinition":
               print("ErrorDefinition")
               pass
            elif top_level_data[self.get_key()] == "UserDefinedValueTypeDefinition":
                print("UserDefinedValueTypeDefinition")
                pass
            else:
                raise StaticException(f"Top level {top_level_data[self.get_key()]} not supported")
    
    def _parse_source_unit(self, data: Dict, filename: str):
        if data[self.get_key()] != "SourceUnit":
            return
        # match any char for filename
        # filename can contain space, /, -, ..
        # filename = solidity/test.sol => name_candiate = ["solidity",]
        name_candidates = re.findall("=+ (.+) =+", filename)
        if name_candidates:
            assert len(name_candidates) == 1
            name: str = name_candidates[0]
        else:
            name = filename
        sourceUnit = -1 
        if "src" in data:
            # Lay ra du lieu cuoi trong src, vi du: src = "12:23:32" -> ket qua la 32
            sourceUnit_candidates = re.findall("[0-9]*:[0-9]*:([0-9]*)", data["src"])
            if len(sourceUnit_candidates) == 1:
                sourceUnit = int(sourceUnit_candidates[0])
        if sourceUnit == -1:
            print("source Unit not found")
            return

        self._compilation_unit.source_units[sourceUnit] = name
        if os.path.isfile(name) and not name in self._compilation_unit.core.source_code:
            self._compilation_unit.core.add_source_code(name)
    
    def parse_contracts(self):
        if not self._underlying_contract_to_parser:
            print(f"No contract were found in {self._compilation_unit.core.filename}, check the correct compilation")
        if self._parsed:
            raise Exception("Contract analysis can be run only once!")
        # First we save all the contracts in a dict
        # the key is the contractid
        for contract in self._underlying_contract_to_parser:
            self._contracts_by_id[contract.id] = contract
            self._compilation_unit.contracts.append(contract)
        
        for contract_parser in self._underlying_contract_to_parser.values():
            
            ancestors = []
            fathers = []
            father_constructors = []

            for i in contract_parser.linearized_base_contracts[1:]:
                if i in self._contracts_by_id:
                    ancestors.append(self._contracts_by_id[i])
                else:
                    contract_parser.log_incorrect_parsing("error")
            
            for i in contract_parser.baseContracts:
                if i in self._contracts_by_id:
                    fathers.append(self._contracts_by_id[i])
                else:
                    contract_parser.log_incorrect_parsing("error")
            
            for i in contract_parser.baseConstructorContractsCalled:
                
                if i in self._contracts_by_id:
                    father_constructors.append(self._contracts_by_id[i])
                else:
                    contract_parser.log_incorrect_parsing("error")

            contract_parser.underlying_contract.set_inheritance(
                ancestors, fathers, father_constructors
            )
        
        contracts_to_be_analyzed = list(self._underlying_contract_to_parser.values())
        
        libraries = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind == "library"
        ]
        contracts_to_be_analyzed = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind != "library"
        ]
        self._analyze_all_enums(contracts_to_be_analyzed)
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        # We first parse the struct/variables/functions/contract
        self._parse_first_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        # We analyze the struct and parse and analyze the events
        self._parse_second_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
         # Then we analyse state variables, functions and modifiers
        self._parse_third_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        self._parsed = True
    
    def _analyze_all_enums(self, contracts_to_be_analyzed: List[ContractSolc]):
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            # Duyet tat cac contract cha cua contract duoc xet neu tat ca contract duoc xu ly thi tra ve true
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )
            # Thuc hien khi contract duoc xet khong co ke thua hoac tat ca contract deu duoc phan tich
            if not contract.underlying_contract.inheritance or all_father_analyzed:

                self._analyze_enums(contract)
            else:
                contracts_to_be_analyzed += [contract]

    def _analyze_enums(self, contract: ContractSolc):
        # Enum must be analyzed first
        contract.analyze_enums()
        contract.set_is_analyzed(True)

    def _parse_first_part(
        self, 
        contracts_to_be_analyzed: List[ContractSolc], 
        libraries: List[ContractSolc]
    ):
        """
        This functions will parse the struct/variables/functions/contract
        """
        for lib in libraries:
            self._parse_struct_var_modifiers_functions(lib)
        
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]
            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )
            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._parse_struct_var_modifiers_functions(contract)
            else:
                contracts_to_be_analyzed += [contract]
    
    def _parse_second_part(
        self,
        contracts_to_be_analyzed: List[ContractSolc],
        libraries: List[ContractSolc],
    ):
        """
        This functions will parse the struct/event
        """
        for lib in libraries:
            self._analyze_struct_events(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._analyze_struct_events(contract)

            else:
                contracts_to_be_analyzed += [contract]
    def _parse_third_part(
        self,
        contracts_to_be_analyzed: List[ContractSolc],
        libraries: List[ContractSolc],
    ):
        """
        This functions will parse the variable/modifier/function
        """
        for lib in libraries:
            self._analyze_variables_modifiers_functions(lib)
        
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._analyze_variables_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]
    
    def _parse_struct_var_modifiers_functions(self, contract: ContractSolc, type = "Contract"):
        contract.parse_structs()
        contract.parse_state_variables()
        contract.parse_modifiers()
        contract.parse_functions()
        contract.parse_custom_errors()
        contract.set_is_analyzed(True)
    
    def _analyze_struct_events(self, contract: ContractSolc):
        contract.analyze_constant_state_variables()

        # # Struct can refer to enum, or state variables
        contract.analyze_structs()
        # # Event can refer to struct
        contract.analyze_events()
        contract.analyze_custom_errors()
        contract.set_is_analyzed(True)

    def _analyze_variables_modifiers_functions(self, contract: ContractSolc):
        contract.analyze_params_modifiers()
        contract.analyze_params_functions()
        contract.analyze_state_variables()
        contract.analyze_content_modifiers()
        contract.analyze_content_functions()
        contract.set_is_analyzed(True)

    def analyze_contracts(self): 
        if not self._parsed:
            raise StaticException("Parse the contract before running analyses")
        self._convert_to_astir()

        # compute_dependency(self._compilation_unit)
        # self._compilation_unit.compute_storage_layout()
        # self._analyzed = True
    def _convert_to_astir(self):
       for contract in self._compilation_unit.contracts:
            # contract.add_constructor_variables()
            for func in contract.functions:
                try: 
                    func.generate_astir_and_analyze()
                except AttributeError as e:
                    # This can happens for example if there is a call to an interface
                    # And the interface is redefined due to contract's name reuse
                    # But the available version misses some functions
                    self._underlying_contract_to_parser[contract].log_incorrect_parsing(
                        f"Impossible to generate IR for {contract.name}.{func.name} ({func.source_mapping}):\n {e}"
                    )