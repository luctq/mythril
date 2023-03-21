import re
import linecache
from abc import ABCMeta
from typing import Dict, Union, List, Tuple, TYPE_CHECKING, Optional

from crytic_compile.utils.naming import Filename

from mythril.ast.core.context.context import Context

if TYPE_CHECKING:
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
class Source: 
    def __init__(self) -> None:
        self.start: int = 0
        self.length: int = 0
        self.filename: Filename = Filename("", "", "", "")
        self.is_dependency: bool = False
        self.lines: List[int] = []
        self.code: str = ""
        self.starting_column: int = 0
        self.ending_column: int = 0
        self.end: int = 0
        self.compilation_unit: Optional["StaticCompilationUnit"] = None

    def get_lines_str(self, line_descr=""):

        # If the compilation unit was not initialized, it means that the set_offset was never called
        # on the corresponding object, which should not happen
        assert self.compilation_unit is not None

        line_prefix = self.compilation_unit.core.line_prefix

        lines = self.lines
        if not lines:
            lines = ""
        elif len(lines) == 1:
            lines = f"{line_prefix}{line_descr}{lines[0]}"
        else:
            lines = f"{line_prefix}{line_descr}{lines[0]}-{line_descr}{lines[-1]}"
        return lines
    
    def __str__(self) -> str:
        lines = self.get_lines_str()
        filename_short: str = self.filename.short if self.filename.short else ""
        return f"{filename_short}{lines}"

    
def _compute_line(
    compilation_unit: "StaticCompilationUnit", filename: Filename, start: int, length: int
) -> Tuple[List[int], int, int]:
    """
    Compute line(s) numbers and starting/ending columns
    from a start/end offset. All numbers start from 1.

    Not done in an efficient way
    """
    start_line, starting_column = compilation_unit.core.crytic_compile.get_line_from_offset(
        filename, start
    )
    end_line, ending_column = compilation_unit.core.crytic_compile.get_line_from_offset(
        filename, start + length
    )
    return list(range(start_line, end_line + 1)), starting_column, ending_column

def _convert_source_mapping(
    offset: str, compilation_unit: "StaticCompilationUnit"
) -> Source:  # pylint: disable=too-many-locals
    """
    Convert a text offset to a real offset
    see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings
    Returns:
        (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
    """
    sourceUnits = compilation_unit.source_units

    position = re.findall("([0-9]*):([0-9]*):([-]?[0-9]*)", offset)
    if len(position) != 1:
        return Source()

    s, l, f = position[0]
    s = int(s)
    l = int(l)
    f = int(f)

    if f not in sourceUnits:
        new_source = Source()
        new_source.start = s
        new_source.length = l
        return new_source
    filename_used = sourceUnits[f]

    # If possible, convert the filename to its absolute/relative version
    assert compilation_unit.core.crytic_compile

    filename: Filename = compilation_unit.core.crytic_compile.filename_lookup(filename_used)
    is_dependency = compilation_unit.core.crytic_compile.is_dependency(filename.absolute)
    (lines, starting_column, ending_column) = _compute_line(compilation_unit, filename, s, l)
    # print("(lines, starting_column, ending_column)", (lines, starting_column, ending_column))
    new_source = Source()
    new_source.start = s
    new_source.length = l
    new_source.filename = filename
    new_source.is_dependency = is_dependency
    new_source.lines = lines
    new_source.starting_column = starting_column
    new_source.ending_column = ending_column
    new_source.end = new_source.start + l
    for i in range(lines[0], lines[-1] + 1):
        new_source.code += linecache.getline(filename.short, i)
    return new_source
class SourceMapping(Context, metaclass=ABCMeta):
    def __init__(self) -> None:
        super().__init__()

        self.source_mapping: Source = Source()
        self.references: List[Source] = []

    def set_offset(
        self, offset: Union["Source", str], compilation_unit: "StaticCompilationUnit"
    ) -> None:
        if isinstance(offset, Source):
            self.source_mapping.start = offset.start
            self.source_mapping.length = offset.length
            self.source_mapping.filename = offset.filename
            self.source_mapping.is_dependency = offset.is_dependency
            self.source_mapping.lines = offset.lines
            self.source_mapping.starting_column = offset.starting_column
            self.source_mapping.ending_column = offset.ending_column
            self.source_mapping.end = offset.end
            for i in range(offset.lines[0], offset.lines[-1] + 1):
                self.source_mapping.code += linecache.getline(offset.filename.short, i)
        else:
            # print("debug")
            self.source_mapping = _convert_source_mapping(offset, compilation_unit)
        self.source_mapping.compilation_unit = compilation_unit
