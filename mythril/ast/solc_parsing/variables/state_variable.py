from typing import Dict

from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.solc_parsing.variables.variable_declaration import VariableDeclarationSolc

class StateVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: StateVariable, variable_data: Dict):
        super().__init__(variable, variable_data)
    