from typing import Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mythril.ast.core.declarations.function import Function
    from mythril.ast.core.declarations.solidity_variables import SolidityFunction, SolidityVariable
    from mythril.ast.core.declarations.contract import Contract
    from mythril.ast.core.variables.variable import Variable

InternalCallType = Union[Function, SolidityFunction]
HighLevelCallType = Tuple[Contract, Union[Function, Variable]]
LibraryCallType = Tuple[Contract, Function]
LowLevelCallType = Tuple[Union[Variable, SolidityVariable], str]
