from enum import Enum
from typing import List

from mythril.ast.core.expressions.expression_typed import ExpressionTyped
from mythril.ast.core.expressions.expression import Expression
from mythril.ast.core.exceptions import StaticCoreError

class BinaryOperationType(Enum):
    POWER = 0  # **
    MULTIPLICATION = 1  # *
    DIVISION = 2  # /
    MODULO = 3  # %
    ADDITION = 4  # +
    SUBTRACTION = 5  # -
    LEFT_SHIFT = 6  # <<
    RIGHT_SHIFT = 7  # >>>
    AND = 8  # &
    CARET = 9  # ^
    OR = 10  # |
    LESS = 11  # <
    GREATER = 12  # >
    LESS_EQUAL = 13  # <=
    GREATER_EQUAL = 14  # >=
    EQUAL = 15  # ==
    NOT_EQUAL = 16  # !=
    ANDAND = 17  # &&
    OROR = 18  # ||

    # YUL specific operators
    # TODO: investigate if we can remove these
    # Find the types earlier on, and do the conversion
    DIVISION_SIGNED = 19
    MODULO_SIGNED = 20
    LESS_SIGNED = 21
    GREATER_SIGNED = 22
    RIGHT_SHIFT_ARITHMETIC = 23

    # pylint: disable=too-many-branches
    @staticmethod
    def get_type(
        operation_type: "BinaryOperation",
    ) -> "BinaryOperationType":
        if operation_type == "**":
            return BinaryOperationType.POWER
        if operation_type == "*":
            return BinaryOperationType.MULTIPLICATION
        if operation_type == "/":
            return BinaryOperationType.DIVISION
        if operation_type == "%":
            return BinaryOperationType.MODULO
        if operation_type == "+":
            return BinaryOperationType.ADDITION
        if operation_type == "-":
            return BinaryOperationType.SUBTRACTION
        if operation_type == "<<":
            return BinaryOperationType.LEFT_SHIFT
        if operation_type == ">>":
            return BinaryOperationType.RIGHT_SHIFT
        if operation_type == "&":
            return BinaryOperationType.AND
        if operation_type == "^":
            return BinaryOperationType.CARET
        if operation_type == "|":
            return BinaryOperationType.OR
        if operation_type == "<":
            return BinaryOperationType.LESS
        if operation_type == ">":
            return BinaryOperationType.GREATER
        if operation_type == "<=":
            return BinaryOperationType.LESS_EQUAL
        if operation_type == ">=":
            return BinaryOperationType.GREATER_EQUAL
        if operation_type == "==":
            return BinaryOperationType.EQUAL
        if operation_type == "!=":
            return BinaryOperationType.NOT_EQUAL
        if operation_type == "&&":
            return BinaryOperationType.ANDAND
        if operation_type == "||":
            return BinaryOperationType.OROR
        if operation_type == "/'":
            return BinaryOperationType.DIVISION_SIGNED
        if operation_type == "%'":
            return BinaryOperationType.MODULO_SIGNED
        if operation_type == "<'":
            return BinaryOperationType.LESS_SIGNED
        if operation_type == ">'":
            return BinaryOperationType.GREATER_SIGNED
        if operation_type == ">>'":
            return BinaryOperationType.RIGHT_SHIFT_ARITHMETIC

        raise StaticCoreError(f"get_type: Unknown operation type {operation_type})")

class BinaryOperation(ExpressionTyped):
    def __init__(
        self,
        left_expression: Expression,
        right_expression: Expression,
        expression_type: BinaryOperationType,
    ) -> None:
        assert isinstance(left_expression, Expression)
        assert isinstance(right_expression, Expression)
        super().__init__()
        self._expressions = [left_expression, right_expression]
        self._type: BinaryOperationType = expression_type

    @property
    def expressions(self) -> List[Expression]:
        return self._expressions

    @property
    def expression_left(self) -> Expression:
        return self._expressions[0]

    @property
    def expression_right(self) -> Expression:
        return self._expressions[1]

    @property
    def type(self) -> BinaryOperationType:
        return self._type

    def __str__(self) -> str:
        return str(self.expression_left) + " " + str(self.type) + " " + str(self.expression_right)
