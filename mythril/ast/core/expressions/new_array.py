from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.solidity_types.type import Type


class NewArray(Expression):

    # note: dont conserve the size of the array if provided
    def __init__(self, depth, array_type):
        super().__init__()
        assert isinstance(array_type, Type)
        self._depth: int = depth
        self._array_type: Type = array_type