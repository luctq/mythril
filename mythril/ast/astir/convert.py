from mythril.ast.astir.expression_to_astir import ExpressionToAstIR
from mythril.ast.core.expressions.literal import Literal
from mythril.ast.core.expressions.identifier import Identifier
from mythril.ast.astir.variables.constant import Constant
from mythril.ast.astir.operations.condition import Condition
from mythril.ast.astir.operations.lvalue import OperationWithLValue
from mythril.ast.astir.operations.return_operation import Return

def convert_expression(expression, node):
    # handle standlone expresUsion
    # such as return true;
    from mythril.ast.core.cfg.node import NodeType

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

    # result = apply_ir_heuristics(result, node)

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

