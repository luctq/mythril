from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.solidity_types.elementary_type import ElementaryType


class NewElementaryType(Expression):
    def __init__(self, new_type):
        assert isinstance(new_type, ElementaryType)
        super().__init__()
        self._type = new_type