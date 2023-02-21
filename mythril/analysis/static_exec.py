from typing import Union, List
from crytic_compile import CryticCompile, InvalidCompilation

from mythril.exceptions import StaticError
from mythril.ast.core.static_exec_core import StaticExecCore
from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
from mythril.ast.core.compilation_unit import StaticCompilationUnit
class StaticExec(StaticExecCore):
    """
    Execute static analyze smart contract
    """ 
    def __init__(self, target: Union[str, CryticCompile], **kwargs):
        super().__init__()
        self._parsers: List[StaticCompilationUnitSolc] = [] 
        try:
            if isinstance(target, CryticCompile):
                crytic_compile = target
            else:
                crytic_compile = CryticCompile(target, **kwargs)
            self._crytic_compile = crytic_compile
        except InvalidCompilation as e:
            # pylint: disable=raise-missing-from
            raise StaticError(f"Invalid compilation: \n{str(e)}")
        for compilation_unit in crytic_compile.compilation_units.values():
            for path, ast in compilation_unit.asts.items():
                print(f"\npath: {path}, ast: {ast}\n")
            compilation_unit_static = StaticCompilationUnit(self, compilation_unit)
            self._compilation_units.append(compilation_unit_static)
            parser = StaticCompilationUnitSolc(compilation_unit_static)
            self._parsers.append(parser)
            for path, ast in compilation_unit.asts.items():
                parser.parse_top_level_from_loaded_json(ast, path) # dong nay quan trong
                self.add_source_code(path)
            # _update_file_scopes(compilation_unit_static.scopes.values())
            # self._init_parsing_and_analyses()
            