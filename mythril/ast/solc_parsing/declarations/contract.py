from typing import List, Dict, Callable, TYPE_CHECKING, Union
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.core.declarations.contract import Contract

if TYPE_CHECKING:
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
class ContractSolc(CallerContextExpression):
    def __init__(self, static_parser: "StaticCompilationUnitSolc", contract: Contract, data):
        self._contract = contract
        self._static_parser = static_parser
        self._data = data
        if self.is_compact_ast:
            self._contract.name = self._data["name"]
            # self._handle_comment(self._data)
        else:
            self._contract.name = self._data["attributes"][self.get_key()]
            # self._handle_comment(self._data["attributes"])
    @property
    def is_compact_ast(self) -> bool:
        return self._static_parser.is_compact_ast
    
    def get_key(self) -> str:
        return self._static_parser.get_key()
    
    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self._contract.compilation_unit

    @property
    def static_parser(self) -> "StaticCompilationUnitSolc":
        return self._slither_parser
