from mythril.ast.core.declarations.function import Function
from mythril.ast.core.children.child_contract import ChildContract
from mythril.ast.core.children.child_inheritance import ChildInheritance
class FunctionContract(Function, ChildContract, ChildInheritance):
    pass
