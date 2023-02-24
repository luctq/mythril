from typing import Optional
from mythril.ast.core.variables.variable import Variable
from mythril.ast.core.children.child_function import ChildFunction

class LocalVariable(ChildFunction, Variable):
    def __init__(self) -> None:
        super().__init__()
        self._location: Optional[str] = None

    
    def set_location(self, loc: str) -> None:
        self._location = loc

    @property
    def location(self) -> Optional[str]:
        """
            Variable Location
            Can be storage/memory or default
        Returns:
            (str)
        """
        return self._location