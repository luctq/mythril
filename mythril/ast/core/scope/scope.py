from crytic_compile.utils.naming import Filename
from typing import Dict, Set

from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.declarations.pragma_directive import Pragma
class FileScope:
    def __init__(self, filename: Filename):
        self.filename = filename
        self.contracts: Dict[str, Contract] = {}
        self.pragmas: Set[Pragma] = set()
