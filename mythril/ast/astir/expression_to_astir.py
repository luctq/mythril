from typing import List
from .expression import ExpressionVisitor
from mythril.ast.astir.operations.operation import Operation
from mythril.ast.astir.operations.return_operation import Return
from mythril.ast.core.declarations.function import Function
from mythril.ast.core.declarations.solidity_variables import SolidityVariable, SolidityFunction, SolidityVariableComposed
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.declarations.enum import Enum
from mythril.ast.core.expressions.assignment_operation import AssignmentOperationType
from mythril.ast.core.expressions.unary_operation import UnaryOperationType
from mythril.ast.core.expressions.binary_operation import BinaryOperationType
from mythril.ast.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from mythril.ast.core.expressions.call_expression import CallExpression
from mythril.ast.core.expressions.identifier import Identifier
from mythril.ast.core.expressions.member_access import MemberAccess
from mythril.ast.core.solidity_types.array_type import ArrayType
from mythril.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.ast.core.solidity_types.type_alias import TypeAlias
from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.variables.variable import Variable
from mythril.ast.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from mythril.ast.astir.exceptions import AstIRError

from mythril.ast.astir.operations.assignment import Assignment
from mythril.ast.astir.operations.index import Index
from mythril.ast.astir.operations.init_array import InitArray
from mythril.ast.astir.operations.member import Member
from mythril.ast.astir.operations.type_conversion import TypeConversion
from mythril.ast.astir.operations.unpack import Unpack
from mythril.ast.astir.operations.return_operation import Return
from mythril.ast.astir.operations.operation import Operation
from mythril.ast.astir.operations.binary import Binary, BinaryType

from mythril.ast.astir.tmp_operations.tmp_new_array import TmpNewArray

from mythril.ast.astir.variables.constant import Constant
from mythril.ast.astir.variables.reference import ReferenceVariable
from mythril.ast.astir.variables.temporary import TemporaryVariable
from mythril.ast.astir.variables.tuple import TupleVariable

key = "expressionToAstIR"
def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def get_without_removing(expression):
    return expression.context[key]


def set_val(expression, val):
    expression.context[key] = val


_binary_to_binary = {
    BinaryOperationType.POWER: BinaryType.POWER,
    BinaryOperationType.MULTIPLICATION: BinaryType.MULTIPLICATION,
    BinaryOperationType.DIVISION: BinaryType.DIVISION,
    BinaryOperationType.MODULO: BinaryType.MODULO,
    BinaryOperationType.ADDITION: BinaryType.ADDITION,
    BinaryOperationType.SUBTRACTION: BinaryType.SUBTRACTION,
    BinaryOperationType.LEFT_SHIFT: BinaryType.LEFT_SHIFT,
    BinaryOperationType.RIGHT_SHIFT: BinaryType.RIGHT_SHIFT,
    BinaryOperationType.AND: BinaryType.AND,
    BinaryOperationType.CARET: BinaryType.CARET,
    BinaryOperationType.OR: BinaryType.OR,
    BinaryOperationType.LESS: BinaryType.LESS,
    BinaryOperationType.GREATER: BinaryType.GREATER,
    BinaryOperationType.LESS_EQUAL: BinaryType.LESS_EQUAL,
    BinaryOperationType.GREATER_EQUAL: BinaryType.GREATER_EQUAL,
    BinaryOperationType.EQUAL: BinaryType.EQUAL,
    BinaryOperationType.NOT_EQUAL: BinaryType.NOT_EQUAL,
    BinaryOperationType.ANDAND: BinaryType.ANDAND,
    BinaryOperationType.OROR: BinaryType.OROR,
}

_signed_to_unsigned = {
    BinaryOperationType.DIVISION_SIGNED: BinaryType.DIVISION,
    BinaryOperationType.MODULO_SIGNED: BinaryType.MODULO,
    BinaryOperationType.LESS_SIGNED: BinaryType.LESS,
    BinaryOperationType.GREATER_SIGNED: BinaryType.GREATER,
    BinaryOperationType.RIGHT_SHIFT_ARITHMETIC: BinaryType.RIGHT_SHIFT,
}


def convert_assignment(left, right, t, return_type):
    if t == AssignmentOperationType.ASSIGN:
        return Assignment(left, right, return_type)
    if t == AssignmentOperationType.ASSIGN_OR:
        return Binary(left, left, right, BinaryType.OR)
    if t == AssignmentOperationType.ASSIGN_CARET:
        return Binary(left, left, right, BinaryType.CARET)
    if t == AssignmentOperationType.ASSIGN_AND:
        return Binary(left, left, right, BinaryType.AND)
    if t == AssignmentOperationType.ASSIGN_LEFT_SHIFT:
        return Binary(left, left, right, BinaryType.LEFT_SHIFT)
    if t == AssignmentOperationType.ASSIGN_RIGHT_SHIFT:
        return Binary(left, left, right, BinaryType.RIGHT_SHIFT)
    if t == AssignmentOperationType.ASSIGN_ADDITION:
        return Binary(left, left, right, BinaryType.ADDITION)
    if t == AssignmentOperationType.ASSIGN_SUBTRACTION:
        return Binary(left, left, right, BinaryType.SUBTRACTION)
    if t == AssignmentOperationType.ASSIGN_MULTIPLICATION:
        return Binary(left, left, right, BinaryType.MULTIPLICATION)
    if t == AssignmentOperationType.ASSIGN_DIVISION:
        return Binary(left, left, right, BinaryType.DIVISION)
    if t == AssignmentOperationType.ASSIGN_MODULO:
        return Binary(left, left, right, BinaryType.MODULO)

    raise AstIRError("Missing type during assignment conversion")


class ExpressionToAstIR(ExpressionVisitor):
    def __init__(self, expression, node):  # pylint: disable=super-init-not-called
        from mythril.ast.core.cfg.node import NodeType  # pylint: disable=import-outside-toplevel

        self._expression = expression
        self._node = node
        self._result: List[Operation] = []
        self._visit_expression(self.expression)
        if node.type == NodeType.RETURN:
            r = Return(get(self.expression))
            r.set_expression(expression)
            self._result.append(r)
        for ir in self._result:
            ir.set_node(node)

    def result(self):
        return self._result
    
    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        if isinstance(left, list):  # tuple expression:
            if isinstance(right, list):  # unbox assigment
                assert len(left) == len(right)
                for idx, _ in enumerate(left):
                    if not left[idx] is None:
                        operation = convert_assignment(
                            left[idx],
                            right[idx],
                            expression.type,
                            expression.expression_return_type,
                        )
                        operation.set_expression(expression)
                        self._result.append(operation)
                set_val(expression, None)
            else:
                assert isinstance(right, TupleVariable)
                for idx, _ in enumerate(left):
                    if not left[idx] is None:
                        index = idx
                        # The following test is probably always true?
                        if (
                            isinstance(left[idx], LocalVariableInitFromTuple)
                            and left[idx].tuple_index is not None
                        ):
                            index = left[idx].tuple_index
                        operation = Unpack(left[idx], right, index)
                        operation.set_expression(expression)
                        self._result.append(operation)
                set_val(expression, None)
        # Tuple with only one element. We need to convert the assignment to a Unpack
        # Ex:
        # (uint a,,) = g()
        elif (
            isinstance(left, LocalVariableInitFromTuple)
            and left.tuple_index is not None
            and isinstance(right, TupleVariable)
        ):
            operation = Unpack(left, right, left.tuple_index)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, None)
        else:
            # Init of array, like
            # uint8[2] var = [1,2];
            if isinstance(right, list):
                operation = InitArray(right, left)
                operation.set_expression(expression)
                self._result.append(operation)
                set_val(expression, left)
            else:
                operation = convert_assignment(
                    left, right, expression.type, expression.expression_return_type
                )
                operation.set_expression(expression)
                self._result.append(operation)
                # Return left to handle
                # a = b = 1;
                set_val(expression, left)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = TemporaryVariable(self._node)

        if expression.type in _signed_to_unsigned:
            new_left = TemporaryVariable(self._node)
            conv_left = TypeConversion(new_left, left, ElementaryType("int256"))
            new_left.set_type(ElementaryType("int256"))
            conv_left.set_expression(expression)
            self._result.append(conv_left)

            if expression.type != BinaryOperationType.RIGHT_SHIFT_ARITHMETIC:
                new_right = TemporaryVariable(self._node)
                conv_right = TypeConversion(new_right, right, ElementaryType("int256"))
                new_right.set_type(ElementaryType("int256"))
                conv_right.set_expression(expression)
                self._result.append(conv_right)
            else:
                new_right = right

            new_final = TemporaryVariable(self._node)
            operation = Binary(new_final, new_left, new_right, _signed_to_unsigned[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

            conv_final = TypeConversion(val, new_final, ElementaryType("uint256"))
            val.set_type(ElementaryType("uint256"))
            conv_final.set_expression(expression)
            self._result.append(conv_final)
        else:
            operation = Binary(val, left, right, _binary_to_binary[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

        set_val(expression, val)

    def _post_call_expression(
        self, expression
    ):
        pass

    def _post_conditional_expression(self, expression):
        pass

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, expression.type)

    def _post_identifier(self, expression):
        set_val(expression, expression.value)

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        # Left can be a type for abi.decode(var, uint[2])
        if isinstance(left, Type):
            # Nested type are not yet supported by abi.decode, so the assumption
            # Is that the right variable must be a constant
            assert isinstance(right, Constant)
            t = ArrayType(left, right.value)
            set_val(expression, t)
            return
        val = ReferenceVariable(self._node)
        # access to anonymous array
        # such as [0,1][x]
        if isinstance(left, list):
            init_array_val = TemporaryVariable(self._node)
            init_array_right = left
            left = init_array_val
            operation = InitArray(init_array_right, init_array_val)
            operation.set_expression(expression)
            self._result.append(operation)
        operation = Index(val, left, right, expression.type)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_literal(self, expression):
        cst = Constant(expression.value, expression.type, expression.subdenomination)
        set_val(expression, cst)

    def _post_member_access(self, expression):
        pass

    def _post_new_array(self, expression):
        val = TemporaryVariable(self._node)
        operation = TmpNewArray(expression.depth, expression.array_type, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_contract(self, expression):
        pass

    def _post_new_elementary_type(self, expression):
        pass

    def _post_tuple_expression(self, expression):
        pass

    def _post_type_conversion(self, expression):
        pass

    def _post_unary_operation(
        self, expression
    ):
       pass
