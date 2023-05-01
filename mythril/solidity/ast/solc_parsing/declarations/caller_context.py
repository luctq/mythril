import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.solidity.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
class CallerContextExpression(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def is_compact_ast(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def compilation_unit(self) -> "StaticCompilationUnit":
        pass

    @abc.abstractmethod
    def get_key(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def static_parser(self) -> "StaticCompilationUnitSolc":
        pass
