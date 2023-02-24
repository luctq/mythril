from typing import TYPE_CHECKING
from mythril.ast.core.solidity_types.type import Type

class TypeAlias(Type):
    def __init__(self, underlying_type: Type, name: str):
        super().__init__()
        self.name = name
        self.underlying_type = underlying_type
    