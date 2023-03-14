import abc
from mythril.ast.core.context.context import Context
from mythril.ast.core.children.child_expression import ChildExpression
from mythril.ast.core.children.child_node import ChildNode


class AbstractOperation(abc.ABC):
    @property
    @abc.abstractmethod
    def read(self):
        """
        Return the list of variables READ
        """
        pass  # pylint: disable=unnecessary-pass

    @property
    @abc.abstractmethod
    def used(self):
        """
        Return the list of variables used
        """
        pass  # pylint: disable=unnecessary-pass


class Operation(Context, ChildExpression, ChildNode, AbstractOperation):
    @property
    def used(self):
        """
        By default used is all the variables read
        """
        return self.read
