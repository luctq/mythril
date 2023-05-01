from collections import defaultdict
from typing import Optional, Dict, List, Set, Union
from crytic_compile import CryticCompile

from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.solidity.ast.core.context.context import Context
from mythril.solidity.ast.core.declarations.contract import Contract

class StaticExecCore(Context):
    def __init__(self):
        super().__init__()
        self._filename: Optional[str] = None
        self._raw_source_code: Dict[str, str] = {}
        self._crytic_compile: Optional[CryticCompile] = None

        self._compilation_units: List[StaticCompilationUnit] = []

        self.line_prefix: str = "#"

        # Use by the echidna printer
        # If true, partial analysis is allowed
        self.no_fail = False
        
    @property
    def compilation_units(self) -> List[StaticCompilationUnit]:
        return list(self._compilation_units)

    def add_compilation_unit(self, compilation_unit: StaticCompilationUnit):
        self._compilation_units.append(compilation_unit)
    
    @property
    def contracts(self) -> List[Contract]:
        if not self._contracts:
            all_contracts = [
                compilation_unit.contracts for compilation_unit in self._compilation_units
            ]
            self._contracts = [item for sublist in all_contracts for item in sublist]
        return self._contracts

    @property
    def source_code(self) -> Dict[str, str]:
        """{filename: source_code (str)}: source code"""
        return self._raw_source_code

    @property
    def filename(self) -> Optional[str]:
        """str: Filename."""
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename
    
    def add_source_code(self, path: str) -> None:
        """
        :param path:
        :return:
        """
        if self.crytic_compile and path in self.crytic_compile.src_content:
            self.source_code[path] = self.crytic_compile.src_content[path]
        else:
            with open(path, encoding="utf8", newline="") as f:
                self.source_code[path] = f.read()
        # print("self.source_code[path]: \n", self.source_code[path])
    
    @property
    def crytic_compile(self) -> Optional[CryticCompile]:
        return self._crytic_compile
