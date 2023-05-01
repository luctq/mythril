from typing import Dict, Optional, List, TYPE_CHECKING
from mythril.solidity.ast.core.variables.structure_variable import StructureVariable

if TYPE_CHECKING: 
    from mythril.solidity.ast.core.compilation_unit import  StaticCompilationUnit
class Structure:
    def __init__(self, compilation_unit: "StaticCompilationUnit") -> None:
        super().__init__()
        self._name: Optional[str] = None
        self._canonical_name: Optional[str] = None
        self._elems: Dict[str, "StructureVariable"] = {}
        # Name of the elements in the order of declaration
        self._elems_ordered: List[str] = []
        self.compilation_unit = compilation_unit

    @property
    def canonical_name(self) -> str:
        assert self._canonical_name
        return self._canonical_name

    @canonical_name.setter
    def canonical_name(self, name: str) -> None:
        self._canonical_name = name

    @property
    def name(self) -> str:
        assert self._name
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def elems(self) -> Dict[str, "StructureVariable"]:
        return self._elems

    def add_elem_in_order(self, s: str) -> None:
        self._elems_ordered.append(s)

    @property
    def elems_ordered(self) -> List["StructureVariable"]:
        ret = []
        for e in self._elems_ordered:
            ret.append(self._elems[e])
        return ret

    def __str__(self) -> str:
        return self.name
