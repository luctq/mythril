from typing import Optional, List

from mythril.ast.core.expressions.expression import Expression


class CallExpression(Expression):  # pylint: disable=too-many-instance-attributes
    def __init__(self, called, arguments, type_call):
        assert isinstance(called, Expression)
        super().__init__()
        self._called: Expression = called
        self._arguments: List[Expression] = arguments
        self._type_call: str = type_call
        # gas and value are only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        self._gas: Optional[Expression] = None
        self._value: Optional[Expression] = None
        self._salt: Optional[Expression] = None