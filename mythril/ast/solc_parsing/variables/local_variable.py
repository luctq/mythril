from typing import Dict

from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.solc_parsing.variables.variable_declaration import VariableDeclarationSolc

class LocalVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: LocalVariable, variable_data: Dict):
        super().__init__(variable, variable_data)
    
    @property
    def underlying_variable(self) -> LocalVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariable)
        return self._variable