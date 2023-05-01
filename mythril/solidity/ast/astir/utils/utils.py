from mythril.solidity.ast.core.variables.local_variable import LocalVariable
from mythril.solidity.ast.core.variables.state_variable import StateVariable

from mythril.solidity.ast.core.declarations.solidity_variables import SolidityVariable
from mythril.solidity.ast.core.variables.top_level_variable import TopLevelVariable

from mythril.solidity.ast.astir.variables.temporary import TemporaryVariable
from mythril.solidity.ast.astir.variables.constant import Constant
from mythril.solidity.ast.astir.variables.reference import ReferenceVariable
from mythril.solidity.ast.astir.variables.tuple import TupleVariable


def is_valid_rvalue(v):
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TopLevelVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            ReferenceVariable,
        ),
    )


def is_valid_lvalue(v):
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            ReferenceVariable,
            TupleVariable,
        ),
    )
