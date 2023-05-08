import abc
from mythril.solidity.ast.core.context.context import Context
from mythril.solidity.ast.core.children.child_expression import ChildExpression
from mythril.solidity.ast.core.children.child_node import ChildNode
from mythril.solidity.ast.utils.unroll import unroll

class AbstractOperation(abc.ABC):
    @property
    @abc.abstractmethod
    def read(self):
        """
        Return the list of variables READ
        """
        pass 

    @property
    @abc.abstractmethod
    def used(self):
        """
        Return the list of variables used
        """
        pass


class Operation(Context, ChildExpression, ChildNode, AbstractOperation):
    @property
    def used(self):
        """
        By default used is all the variables read
        """
        return self.read
    
    @staticmethod
    def _unroll(l):
        return unroll(l)
    
