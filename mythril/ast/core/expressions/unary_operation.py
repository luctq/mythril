from enum import Enum

from mythril.ast.core.exceptions import StaticCoreError
from mythril.ast.core.expressions.expression_typed import ExpressionTyped
from mythril.ast.core.expressions.expression import Expression

class UnaryOperationType(Enum):
    BANG = 0  # !
    TILD = 1  # ~
    DELETE = 2  # delete
    PLUSPLUS_PRE = 3  # ++
    MINUSMINUS_PRE = 4  # --
    PLUSPLUS_POST = 5  # ++
    MINUSMINUS_POST = 6  # --
    PLUS_PRE = 7  # for stuff like uint(+1)
    MINUS_PRE = 8  # for stuff like uint(-1
    @staticmethod
    def get_type(operation_type, isprefix):
        if isprefix:
            if operation_type == "!":
                return UnaryOperationType.BANG
            if operation_type == "~":
                return UnaryOperationType.TILD
            if operation_type == "delete":
                return UnaryOperationType.DELETE
            if operation_type == "++":
                return UnaryOperationType.PLUSPLUS_PRE
            if operation_type == "--":
                return UnaryOperationType.MINUSMINUS_PRE
            if operation_type == "+":
                return UnaryOperationType.PLUS_PRE
            if operation_type == "-":
                return UnaryOperationType.MINUS_PRE
        else:
            if operation_type == "++":
                return UnaryOperationType.PLUSPLUS_POST
            if operation_type == "--":
                return UnaryOperationType.MINUSMINUS_POST
        raise StaticCoreError(f"get_type: Unknown operation type {operation_type}")

class UnaryOperation(ExpressionTyped):
    def __init__(self, expression, expression_type):
        assert isinstance(expression, Expression)
        super().__init__()
        self._expression: Expression = expression
        self._type: UnaryOperationType = expression_type
        if expression_type in [
            UnaryOperationType.DELETE,
            UnaryOperationType.PLUSPLUS_PRE,
            UnaryOperationType.MINUSMINUS_PRE,
            UnaryOperationType.PLUSPLUS_POST,
            UnaryOperationType.MINUSMINUS_POST,
            UnaryOperationType.PLUS_PRE,
            UnaryOperationType.MINUS_PRE,
        ]:
            expression.set_lvalue()
