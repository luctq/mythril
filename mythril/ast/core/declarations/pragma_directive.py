from typing import List, TYPE_CHECKING
from mythril.ast.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from mythril.ast.core.scope.scope import FileScope

class Pragma(SourceMapping):
    def __init__(self, directive: List[str], scope: "FileScope"):
        super().__init__()
        self._directive = directive
        self.scope: "FileScope" = scope
    @property
    def directive(self) -> List[str]:
        """
        list(str)
        """
        return self._directive
