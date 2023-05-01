from pathlib import Path
from typing import Optional, TYPE_CHECKING, Dict

from mythril.solidity.ast.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from mythril.solidity.ast.core.scope.scope import FileScope


class Import(SourceMapping):
    def __init__(self, filename: Path, scope: "FileScope"):
        super().__init__()
        self._filename: Path = filename
        self._alias: Optional[str] = None
        self.scope: "FileScope" = scope
        # Map local name -> original name
        self.renaming: Dict[str, str] = {}