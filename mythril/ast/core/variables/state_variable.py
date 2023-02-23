from typing import Optional, TYPE_CHECKING

from mythril.ast.core.children.child_contract import ChildContract
from mythril.ast.core.variables.variable import Variable

class StateVariable(ChildContract, Variable):
    def __init__(self):
        super().__init__()
        