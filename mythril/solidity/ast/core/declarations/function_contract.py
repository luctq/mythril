from mythril.solidity.ast.core.declarations.function import Function
from mythril.solidity.ast.core.children.child_contract import ChildContract
from mythril.solidity.ast.core.children.child_inheritance import ChildInheritance
from mythril.solidity.ast.core.scope.scope import FileScope
class FunctionContract(Function, ChildContract, ChildInheritance):
    @property
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        if self._canonical_name is None:
            name, parameters, _ = self.signature
            self._canonical_name = (
                ".".join([self.contract_declarer.name] + self._internal_scope + [name])
                + "("
                + ",".join(parameters)
                + ")"
            )
        return self._canonical_name
    
    @property
    def file_scope(self) -> "FileScope":
        return self.contract.file_scope
