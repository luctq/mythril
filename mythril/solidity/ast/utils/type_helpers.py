from typing import Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mythril.solidity.ast.core.declarations.function import Function
    from mythril.solidity.ast.core.declarations.solidity_variables import SolidityFunction, SolidityVariable
    from mythril.solidity.ast.core.declarations.contract import Contract
    from mythril.solidity.ast.core.variables.variable import Variable

InternalCallType = Union[Function, SolidityFunction]
HighLevelCallType = Tuple[Contract, Union[Function, Variable]]
LibraryCallType = Tuple[Contract, Function]
LowLevelCallType = Tuple[Union[Variable, SolidityVariable], str]
