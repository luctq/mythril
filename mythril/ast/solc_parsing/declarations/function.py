from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from mythril.ast.core.declarations.function import Function, FunctionType
from mythril.ast.core.declarations.function_contract import FunctionContract

if TYPE_CHECKING:
    from mythril.ast.solc_parsing.declarations.contract import ContractSolc
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc

class FunctionSolc(CallerContextExpression):
    
    def __init__(
        self,
        function: Function,
        function_data: Dict,
        contract_parser: Optional["ContractSolc"],
        static_parser: "StaticCompilationUnitSolc",
    ):
        self._static_parser: "StaticCompilationUnitSolc" = static_parser
        self._contract_parser = contract_parser
        self._function = function

         # Only present if compact AST
        if self.is_compact_ast:
            self._function.name = function_data["name"]
            if "id" in function_data:
                self._function.id = function_data["id"]
        else:
            self._function.name = function_data["attributes"][self.get_key()]
        
        self._functionNotParsed = function_data
        
        self._analyze_type()
    @property
    def static_parser(self) -> "StaticCompilationUnitSolc":
        return self._static_parser

    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self._function.compilation_unit
    
    def get_key(self) -> str:
        return self._static_parser.get_key()

    def get_children(self, key: str) -> str:
        if self.is_compact_ast:
            return key
        return "children"

    @property
    def is_compact_ast(self):
        return self._static_parser.is_compact_ast
    
    def _analyze_type(self):
        """
        Analyz the type of the function
        Myst be called in the constructor as the name might change according to the function's type
        For example both the fallback and the receiver will have an empty name
        :return:
        """
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed["attributes"]

        if self._function.name == "":
            self._function.function_type = FunctionType.FALLBACK
            # 0.6.x introduced the receiver function
            # It has also an empty name, so we need to check the kind attribute
            if "kind" in attributes:
                if attributes["kind"] == "receive":
                    self._function.function_type = FunctionType.RECEIVE
        else:
            self._function.function_type = FunctionType.NORMAL

        if isinstance(self._function, FunctionContract):
            if self._function.name == self._function.contract_declarer.name:
                self._function.function_type = FunctionType.CONSTRUCTOR