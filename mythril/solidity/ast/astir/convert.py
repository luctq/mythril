from typing import List, TYPE_CHECKING
from mythril.solidity.ast.astir.expression_to_astir import ExpressionToAstIR
from mythril.solidity.ast.core.expressions.literal import Literal
from mythril.solidity.ast.core.expressions.identifier import Identifier
from mythril.solidity.ast.astir.variables.constant import Constant
from mythril.solidity.ast.astir.operations.operation import Operation
from mythril.solidity.ast.astir.operations.condition import Condition
from mythril.solidity.ast.astir.operations.lvalue import OperationWithLValue
from mythril.solidity.ast.astir.operations.return_operation import Return
from mythril.solidity.ast.astir.operations.index import Index
from mythril.solidity.ast.astir.operations.member import Member
from mythril.solidity.ast.astir.operations.delete import Delete
from mythril.solidity.ast.astir.variables.reference import ReferenceVariable

if TYPE_CHECKING:
    from mythril.solidity.ast.core.cfg.node import Node
def convert_expression(expression, node):
    # handle standlone expresUsion
    # such as return true;
    from mythril.solidity.ast.core.cfg.node import NodeType
    
    if isinstance(expression, Literal) and node.type in [NodeType.IF, NodeType.IFLOOP]:
        cst = Constant(expression.value, expression.type)
        cond = Condition(cst)
        cond.set_expression(expression)
        cond.set_node(node)
        result = [cond]
        return result
    if isinstance(expression, Identifier) and node.type in [
        NodeType.IF,
        NodeType.IFLOOP,
    ]:
        cond = Condition(expression.value)
        cond.set_expression(expression)
        cond.set_node(node)
        result = [cond]
        return result
    
    visitor = ExpressionToAstIR(expression, node)
    result = visitor.result()

    for ir in result:
        if isinstance(ir, (Index, Member)):
            ir.lvalue.points_to = ir.variable_left
        if isinstance(ir, Delete):
            if isinstance(ir.lvalue, ReferenceVariable):
                ir.lvalue = ir.lvalue.points_to

    if result:
        if node.type in [NodeType.IF, NodeType.IFLOOP]:
            assert isinstance(result[-1], (OperationWithLValue))
            cond = Condition(result[-1].lvalue)
            cond.set_expression(expression)
            cond.set_node(node)
            result.append(cond)
        elif node.type == NodeType.RETURN:
            # May return None
            if isinstance(result[-1], (OperationWithLValue)):
                r = Return(result[-1].lvalue)
                r.set_expression(expression)
                r.set_node(node)
                result.append(r)

    return result
