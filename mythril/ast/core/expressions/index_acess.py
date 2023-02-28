from typing import List, TYPE_CHECKING

from mythril.ast.core.expressions.expression_typed import ExpressionTyped


if TYPE_CHECKING:
    from mythril.ast.core.expressions.expression import Expression
    from mythril.ast.core.solidity_types.type import Type


class IndexAccess(ExpressionTyped):
    def __init__(self, left_expression, right_expression, index_type):
        super().__init__()
        self._expressions = [left_expression, right_expression]
        # TODO type of undexAccess is not always a Type
        #        assert isinstance(index_type, Type)
        self._type: "Type" = index_type