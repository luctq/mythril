from typing import Union, List, Optional
from crytic_compile import CryticCompile, InvalidCompilation

from mythril.exceptions import StaticError
from mythril.solidity.ast.core.static_exec_core import StaticExecCore
from mythril.solidity.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.analysis.module import ModuleLoader, EntryPoint
from mythril.analysis.module.base import ModuleType
class StaticExec(StaticExecCore):
    """
    Execute static analyze smart contract
    """ 
    def __init__(self,
                 target: Union[str, CryticCompile], modules: Optional[List[str]] = None, **kwargs):
        super().__init__()
        self._parsers: List[StaticCompilationUnitSolc] = [] 
        try:
            if isinstance(target, CryticCompile):
                crytic_compile = target
            else:
                self.filename = target
                crytic_compile = CryticCompile(target, **kwargs)
            self._crytic_compile = crytic_compile
        except InvalidCompilation as e:
            raise StaticError(f"Invalid compilation: \n{str(e)}")
        
        for compilation_unit in crytic_compile.compilation_units.values():
            compilation_unit_static = StaticCompilationUnit(self, compilation_unit)
            self._compilation_units.append(compilation_unit_static)
            parser = StaticCompilationUnitSolc(compilation_unit_static)
            self._parsers.append(parser)
            for path, ast in compilation_unit.asts.items():
                parser.parse_top_level_of_ast(ast, path)
                # self.add_source_code(path)
            # _update_file_scopes(compilation_unit_static.scopes.values())
        
        self._init_parsing_and_analyses()
        for module in ModuleLoader().get_detection_modules(EntryPoint.CALLBACK, modules):
            if module.type == ModuleType.STATIC:
                module.set_up(parser.compilation_unit)
                module.execute_static()

    def _init_parsing_and_analyses(self) -> None:
        for parser in self._parsers:
            try:
                parser.parse_contracts()
            except Exception as e:
                raise e
        for parser in self._parsers:
            try:
                parser.analyze_contracts()
            except Exception as e:
                raise e
            