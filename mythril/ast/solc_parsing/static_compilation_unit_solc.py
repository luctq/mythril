import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict

from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.core.compilation_unit import StaticCompilationUnit
from mythril.ast.solc_parsing.declarations.contract import ContractSolc
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.solc_parsing.declarations.structure_top_level import StructureTopLevelSolc
from mythril.ast.solc_parsing.declarations.custom_error import CustomErrorSolc
from mythril.ast.solc_parsing.declarations.function import FunctionSolc
from mythril.ast.core.declarations.pragma_directive import Pragma
from mythril.exceptions import StaticException
class StaticCompilationUnitSolc(CallerContextExpression):
    def __init__(self, compilation_unit: StaticCompilationUnit):
        super().__init__();
        self._contracts_by_id: Dict[int, ContractSolc] = {}
        self._parsed = False
        self._analyzed = False

        self._underlying_contract_to_parser: Dict[Contract, ContractSolc] = {}
        self._structures_top_level_parser: List[StructureTopLevelSolc] = []
        self._custom_error_parser: List[CustomErrorSolc] = []
        # self._variables_top_level_parser: List[TopLevelVariableSolc] = []
        self._functions_top_level_parser: List[FunctionSolc] = []
        # self._using_for_top_level_parser: List[UsingForTopLevelSolc] = []

        self._is_compact_ast = False
        # # self._core: SlitherCore = core
        self._compilation_unit = compilation_unit

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

    def parse_top_level_from_loaded_json(
        self, data_loaded: Dict, filename: str
    ):
        """This function parse data from bytecode ast json. 
        Each node will have its own task, so we will separate 
        and handle each task"""
        if "nodeType" in data_loaded:
            self._is_compact_ast = True

        if data_loaded[self.get_key()] == "root":
            # solc <0.4 is not supported
            return
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
                if self._is_compact_ast:
                    pragma = Pragma(top_level_data["literals"], scope)
                    scope.pragmas.add(pragma)
                else:
                    pragma = Pragma(top_level_data["attributes"]["literals"], scope)
                    scope.pragmas.add(pragma)
                pragma.set_offset(top_level_data["src"], self._compilation_unit)
                self._compilation_unit.pragma_directives.append(pragma)
            # handle later
            elif top_level_data[self.get_key()] == "UsingForDirective":
               print("UsingForDirective")
               pass

            elif top_level_data[self.get_key()] == "ImportDirective":
               print("ImportDirective")
               pass

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
        name_candidates = re.findall("=+ (.+) =+", filename)
        if name_candidates:
            assert len(name_candidates) == 1
            name: str = name_candidates[0]
        else:
            name = filename
        sourceUnit = -1  # handle old solc, or error
        if "src" in data:
            sourceUnit_candidates = re.findall("[0-9]*:[0-9]*:([0-9]*)", data["src"])
            if len(sourceUnit_candidates) == 1:
                sourceUnit = int(sourceUnit_candidates[0])
        if sourceUnit == -1:
            # if source unit is not found
            # We can still deduce it, by assigning to the last source_code added
            # This works only for crytic compile.
            # which used --combined-json ast, rather than --ast-json
            # As a result -1 is not used as index
            if self._compilation_unit.core.crytic_compile is not None:
                sourceUnit = len(self._compilation_unit.core.source_code)

        self._compilation_unit.source_units[sourceUnit] = name
        if os.path.isfile(name) and not name in self._compilation_unit.core.source_code:
            self._compilation_unit.core.add_source_code(name)
        else:
            lib_name = os.path.join("node_modules", name)
            if os.path.isfile(lib_name) and not name in self._compilation_unit.core.source_code:
                self._compilation_unit.core.add_source_code(lib_name)
    
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
        
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        
        contracts_to_be_analyzed = list(self._underlying_contract_to_parser.values())
        libraries = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind == "library"
        ]
        contracts_to_be_analyzed = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind != "library"
        ]
        for lib in libraries:
            self._parse_struct_var_modifiers_functions(lib)
            self._analyze_variables_modifiers_functions(lib)

        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]
            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )
            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._parse_struct_var_modifiers_functions(contract)
                self._analyze_variables_modifiers_functions(contract)
            else:
                contracts_to_be_analyzed += [contract]
        # # We first parse the struct/variables/functions/contract
        # self._parse_first_part(contracts_to_be_analyzed, libraries)
        # [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        # # We analyze the struct and parse and analyze the events
        # # A contract can refer in the variables a struct or a event from any contract
        # # (without inheritance link)
        # self._parse_second_part(contracts_to_be_analyzed, libraries)
        # [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        # # Then we analyse state variables, functions and modifiers
        # self._parse_third_part(contracts_to_be_analyzed, libraries)
        # [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]
        self._parsed = True
    def _parse_execute(
        self, 
        contracts_to_be_analyzed: List[ContractSolc], 
        libraries: List[ContractSolc]
    ):
        """
        This functions will parse the struct/variables/functions/contract
        """
        for lib in libraries:
            self._parse_struct_var_modifiers_functions(lib)
            self._analyze_variables_modifiers_functions(lib)
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]
            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )
            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._parse_struct_var_modifiers_functions(contract)
                self._analyze_variables_modifiers_functions(contract)
            else:
                contracts_to_be_analyzed += [contract]
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
        pass
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
    
    def _parse_struct_var_modifiers_functions(self, contract: ContractSolc):
        # contract.parse_structs()
        contract.parse_state_variables()
        # contract.parse_modifiers()
        contract.parse_functions()
        # contract.parse_custom_errors()
        contract.set_is_analyzed(True)
    
    def _analyze_variables_modifiers_functions(self, contract: ContractSolc):
        # contract.analyze_params_modifiers()
        # ham nay de parse cac bien cho funtion
        contract.analyze_params_functions()
        # self._analyze_params_top_level_function()
        # self._analyze_params_custom_error()

        contract.analyze_state_variables()

        # contract.analyze_content_modifiers()
        # cho nay de phan tich content function
        contract.analyze_content_functions()
        # self._analyze_content_top_level_function()

        # contract.set_is_analyzed(True)
        pass
    def analyze_contracts(self):  # pylint: disable=too-many-statements,too-many-branches
        print("\n================ANALYZE CONTRACT================\n")
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