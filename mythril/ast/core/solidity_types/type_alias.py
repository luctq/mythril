from typing import TYPE_CHECKING, Tuple
from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.children.child_contract import ChildContract

if TYPE_CHECKING:
    from mythril.ast.core.declarations import Contract


class TypeAlias(Type):
    def __init__(self, underlying_type: Type, name: str):
        super().__init__()
        self.name = name
        self.underlying_type = underlying_type

    @property
    def type(self) -> Type:
        """
        Return the underlying type. Alias for underlying_type


        Returns:
            Type: the underlying type

        """
        return self.underlying_type

    @property
    def storage_size(self) -> Tuple[int, bool]:
        return self.underlying_type.storage_size

    def __hash__(self):
        return hash(str(self))

    @property
    def is_dynamic(self) -> bool:
        return self.underlying_type.is_dynamic
    
class TypeAliasContract(TypeAlias, ChildContract):
    def __init__(self, underlying_type: Type, name: str, contract: "Contract"):
        super().__init__(underlying_type, name)
        self._contract: "Contract" = contract

    def __str__(self):
        return self.contract.name + "." + self.name
