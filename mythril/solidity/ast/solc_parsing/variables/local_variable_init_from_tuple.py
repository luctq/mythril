from typing import Dict

from mythril.solidity.ast.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from mythril.solidity.ast.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple


class LocalVariableInitFromTupleSolc(VariableDeclarationSolc):
    def __init__(self, variable: LocalVariableInitFromTuple, variable_data: Dict, index: int):
        super().__init__(variable, variable_data)
        variable.tuple_index = index

    @property
    def underlying_variable(self) -> LocalVariableInitFromTuple:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariableInitFromTuple)
        return self._variable
