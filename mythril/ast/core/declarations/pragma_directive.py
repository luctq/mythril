from typing import List, TYPE_CHECKING
from mythril.ast.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from mythril.ast.core.cfg.scope import FileScope

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
    
    @property
    def version(self) -> str:
        return "".join(self.directive[1:])

    @property
    def name(self) -> str:
        return self.version

    @property
    def is_solidity_version(self) -> bool:
        if len(self._directive) > 0:
            return self._directive[0].lower() == "solidity"
        return False
    
    def __str__(self):
        return "pragma " + "".join(self.directive)
