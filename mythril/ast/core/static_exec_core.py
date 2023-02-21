from collections import defaultdict
from typing import Optional, Dict, List, Set, Union
from crytic_compile import CryticCompile

from mythril.ast.core.compilation_unit import StaticCompilationUnit
from mythril.ast.core.context.context import Context
from mythril.ast.core.declarations.contract import Contract

class StaticExecCore(Context):
    def __init__(self):
        super().__init__()
        self._filename: Optional[str] = None
        self._raw_source_code: Dict[str, str] = {}
        self._source_code_to_line: Optional[Dict[str, List[str]]] = None

        self._previous_results_filename: str = "slither.db.json"
        self._results_to_hide: List = []
        self._previous_results: List = []
        # From triaged result
        self._previous_results_ids: Set[str] = set()
        # Every slither object has a list of result from detector
        # Because of the multiple compilation support, we might analyze
        # Multiple time the same result, so we remove duplicates
        self._currently_seen_resuts: Set[str] = set()
        self._paths_to_filter: Set[str] = set()

        self._crytic_compile: Optional[CryticCompile] = None

        self._generate_patches = False
        self._exclude_dependencies = False

        self._markdown_root = ""

        # If set to true, slither will not catch errors during parsing
        self._disallow_partial: bool = False
        self._skip_assembly: bool = False

        self._show_ignored_findings = False

        # Maps from file to detector name to the start/end ranges for that detector.
        # Infinity is used to signal a detector has no end range.
        self._ignore_ranges: defaultdict[str, defaultdict[str, List[(int, int)]]] = defaultdict(
            lambda: defaultdict(lambda: [])
        )

        self._compilation_units: List[StaticCompilationUnit] = []

        # self._contracts: List[Contract] = []
        # self._contracts_derived: List[Contract] = []

        # self._offset_to_objects: Optional[Dict[Filename, Dict[int, Set[SourceMapping]]]] = None
        # self._offset_to_references: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None
        # self._offset_to_implementations: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None
        # self._offset_to_definitions: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None

        # Line prefix is used during the source mapping generation
        # By default we generate file.sol#1
        # But we allow to alter this (ex: file.sol:1) for vscode integration
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

        # self.parse_ignore_comments(path)
    
    @property
    def crytic_compile(self) -> Optional[CryticCompile]:
        return self._crytic_compile
