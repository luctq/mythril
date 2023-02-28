from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.expressions.expression_typed import ExpressionTyped

from mythril.ast.core.solidity_types.type import Type


class MemberAccess(ExpressionTyped):
    def __init__(self, member_name, member_type, expression):
        # assert isinstance(member_type, Type)
        # TODO member_type is not always a Type
        assert isinstance(expression, Expression)
        super().__init__()
        self._type: Type = member_type
        self._member_name: str = member_name
        self._expression: Expression = expression