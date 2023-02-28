from typing import Optional, Union, TYPE_CHECKING

from mythril.ast.core.expressions.expression import Expression

if TYPE_CHECKING:
    from mythril.ast.core.solidity_types.type import Type


class Literal(Expression):
    def __init__(
        self, value: Union[int, str], custom_type: "Type", subdenomination: Optional[str] = None
    ):
        super().__init__()
        self._value = value
        self._type = custom_type
        self._subdenomination = subdenomination
