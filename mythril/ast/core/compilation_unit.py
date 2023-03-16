from typing import Optional, Dict, List, Set, Union, TYPE_CHECKING, Tuple
from crytic_compile import CompilationUnit, CryticCompile
from crytic_compile.utils.naming import Filename

from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.context.context import Context
from mythril.ast.core.scope.scope import FileScope
from mythril.ast.core.declarations.pragma_directive import Pragma
from mythril.ast.core.declarations.function import Function
if TYPE_CHECKING:
    from mythril.ast.core.static_exec_core import StaticExecCore

class StaticCompilationUnit(Context):
    def __init__(self, core: "StaticExecCore", crytic_compilation_unit: CompilationUnit):
        super().__init__()
        
        self._core = core
        self._crytic_compile_compilation_unit = crytic_compilation_unit
        self.contracts: List[Contract] = []
        self._source_units: Dict[int, str] = {}
        self._pragma_directives: List[Pragma] = []
        self.scopes: Dict[Filename, FileScope] = {}

        self._all_functions: Set[Function] = set()

        self.counter_astir_temporary = 0
    
    @property
    def source_units(self) -> Dict[int, str]:
        return self._source_units

    @property
    def contracts_derived(self) -> List[Contract]:
        """list(Contract): List of contracts that are derived and not inherited."""
        inheritances = [x.inheritance for x in self.contracts]
        inheritance = [item for sublist in inheritances for item in sublist]
        return [c for c in self.contracts if c not in inheritance and not c.is_top_level]

    @property
    def solc_version(self) -> str:
        return self._crytic_compile_compilation_unit.compiler_version.version

    @property
    def core(self) -> "StaticExecCore":
        return self._core
    
    @property
    def pragma_directives(self) -> List[Pragma]:
        """list(core.declarations.Pragma): Pragma directives."""
        return self._pragma_directives

    @property
    def functions(self) -> List[Function]:
        return list(self._all_functions)

    def add_function(self, func: Function):
        self._all_functions.add(func)

    def get_scope(self, filename_str: str) -> FileScope:
        filename = self._crytic_compile_compilation_unit.crytic_compile.filename_lookup(
            filename_str
        )

        if filename not in self.scopes:
            self.scopes[filename] = FileScope(filename)

        return self.scopes[filename]
   