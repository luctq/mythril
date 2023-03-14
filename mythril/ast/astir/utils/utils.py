from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.core.variables.state_variable import StateVariable

from mythril.ast.core.declarations.solidity_variables import SolidityVariable
from mythril.ast.core.variables.top_level_variable import TopLevelVariable

from mythril.ast.astir.variables.temporary import TemporaryVariable
from mythril.ast.astir.variables.constant import Constant
from mythril.ast.astir.variables.reference import ReferenceVariable
from mythril.ast.astir.variables.tuple import TupleVariable


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
