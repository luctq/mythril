from crytic_compile.utils.naming import Filename
from typing import Dict, Set, TYPE_CHECKING

from mythril.solidity.ast.core.solidity_types.type_alias import TypeAlias
from mythril.solidity.ast.core.declarations.import_directive import Import

if TYPE_CHECKING:
    from mythril.solidity.ast.core.declarations.contract import Contract
    from mythril.solidity.ast.core.declarations.pragma_directive import Pragma
class FileScope:
    def __init__(self, filename: Filename):
        self.filename = filename
        self.contracts: Dict[str, Contract] = {}
        self.pragmas: Set[Pragma] = set()
        self.imports: Set[Import] = set()

         # Renamed created by import
        # import A as B
        # local name -> original name (A -> B)
        self.renaming: Dict[str, str] = {}

        # User defined types
        # Name -> type alias
        self.user_defined_types: Dict[str, TypeAlias] = {}
