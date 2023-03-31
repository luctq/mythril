from mythril.ast.core.children.child_contract import ChildContract
from mythril.ast.core.declarations.structure import Structure


class StructureContract(Structure, ChildContract):
    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract
