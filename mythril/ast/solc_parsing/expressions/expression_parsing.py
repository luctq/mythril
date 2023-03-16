import re
from typing import TYPE_CHECKING, Dict

from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression

from mythril.ast.core.expressions.expression import Expression
from mythril.ast.solc_parsing.exceptions import ParsingError
from mythril.ast.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from mythril.ast.core.expressions.binary_operation import BinaryOperation, BinaryOperationType
from mythril.ast.core.expressions.conditional_expression import ConditionalExpression
from mythril.ast.core.expressions.assignment_operation import AssignmentOperation, AssignmentOperationType
from mythril.ast.core.expressions.identifier import Identifier
from mythril.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.ast.core.expressions.literal import Literal
from mythril.ast.solc_parsing.expressions.find_variable import find_variable

def filter_name(value: str) -> str:
    value = value.replace(" memory", "")
    value = value.replace(" storage", "")
    value = value.replace(" external", "")
    value = value.replace(" internal", "")
    value = value.replace("struct ", "")
    value = value.replace("contract ", "")
    value = value.replace("enum ", "")
    value = value.replace(" ref", "")
    value = value.replace(" pointer", "")
    value = value.replace(" pure", "")
    value = value.replace(" view", "")
    value = value.replace(" constant", "")
    value = value.replace(" payable", "")
    value = value.replace("function (", "function(")
    value = value.replace("returns (", "returns(")
    value = value.replace(" calldata", "")

    # remove the text remaining after functio(...)
    # which should only be ..returns(...)
    # nested parenthesis so we use a system of counter on parenthesis
    idx = value.find("(")
    if idx:
        counter = 1
        max_idx = len(value)
        while counter:
            assert idx < max_idx
            idx = idx + 1
            if value[idx] == "(":
                counter += 1
            elif value[idx] == ")":
                counter -= 1
        value = value[: idx + 1]
    return value
def parse_expression(expression: Dict, caller_context: CallerContextExpression) -> "Expression":
    """

    Returns:
        str: expression
    """
    #  Expression
    #    = Expression ('++' | '--')
    #    | NewExpression
    #    | IndexAccess
    #    | MemberAccess
    #    | FunctionCall
    #    | '(' Expression ')'
    #    | ('!' | '~' | 'delete' | '++' | '--' | '+' | '-') Expression
    #    | Expression '**' Expression
    #    | Expression ('*' | '/' | '%') Expression
    #    | Expression ('+' | '-') Expression
    #    | Expression ('<<' | '>>') Expression
    #    | Expression '&' Expression
    #    | Expression '^' Expression
    #    | Expression '|' Expression
    #    | Expression ('<' | '>' | '<=' | '>=') Expression
    #    | Expression ('==' | '!=') Expression
    #    | Expression '&&' Expression
    #    | Expression '||' Expression
    #    | Expression '?' Expression ':' Expression
    #    | Expression ('=' | '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%=') Expression
    #    | PrimaryExpression
    # The AST naming does not follow the spec
    assert isinstance(caller_context, CallerContextExpression)
    name = expression[caller_context.get_key()]
    is_compact_ast = caller_context.is_compact_ast
    src = expression["src"]

    if name == "UnaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        assert "prefix" in attributes
        operation_type = UnaryOperationType.get_type(attributes["operator"], attributes["prefix"])

        if is_compact_ast:
            expression = parse_expression(expression["subExpression"], caller_context)
        else:
            assert len(expression["children"]) == 1
            expression = parse_expression(expression["children"][0], caller_context)
        unary_op = UnaryOperation(expression, operation_type)
        unary_op.set_offset(src, caller_context.compilation_unit)
        return unary_op

    if name == "BinaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        operation_type = BinaryOperationType.get_type(attributes["operator"])

        if is_compact_ast:
            left_expression = parse_expression(expression["leftExpression"], caller_context)
            right_expression = parse_expression(expression["rightExpression"], caller_context)
        else:
            assert len(expression["children"]) == 2
            left_expression = parse_expression(expression["children"][0], caller_context)
            right_expression = parse_expression(expression["children"][1], caller_context)
        binary_op = BinaryOperation(left_expression, right_expression, operation_type)
        binary_op.set_offset(src, caller_context.compilation_unit)
        return binary_op

    if name in "FunctionCall":
        pass

    if name == "FunctionCallOptions":
        pass

    if name == "TupleExpression":
        pass

    if name == "Conditional":
        if is_compact_ast:
            if_expression = parse_expression(expression["condition"], caller_context)
            then_expression = parse_expression(expression["trueExpression"], caller_context)
            else_expression = parse_expression(expression["falseExpression"], caller_context)
        else:
            children = expression["children"]
            assert len(children) == 3
            if_expression = parse_expression(children[0], caller_context)
            then_expression = parse_expression(children[1], caller_context)
            else_expression = parse_expression(children[2], caller_context)
        conditional = ConditionalExpression(if_expression, then_expression, else_expression)
        conditional.set_offset(src, caller_context.compilation_unit)
        return conditional

    if name == "Assignment":
        if is_compact_ast:
            left_expression = parse_expression(expression["leftHandSide"], caller_context)
            right_expression = parse_expression(expression["rightHandSide"], caller_context)

            operation_type = AssignmentOperationType.get_type(expression["operator"])

            operation_return_type = expression["typeDescriptions"]["typeString"]
        else:
            attributes = expression["attributes"]
            children = expression["children"]
            assert len(expression["children"]) == 2
            left_expression = parse_expression(children[0], caller_context)
            right_expression = parse_expression(children[1], caller_context)

            operation_type = AssignmentOperationType.get_type(attributes["operator"])
            operation_return_type = attributes["type"]

        assignement = AssignmentOperation(
            left_expression, right_expression, operation_type, operation_return_type
        )
        assignement.set_offset(src, caller_context.compilation_unit)
        return assignement

    if name == "Literal":
        subdenomination = None

        assert "children" not in expression

        if is_compact_ast:
            value = expression.get("value", None)
            if value:
                if "subdenomination" in expression and expression["subdenomination"]:
                    subdenomination = expression["subdenomination"]
            elif not value and value != "":
                value = "0x" + expression["hexValue"]
            type_candidate = expression["typeDescriptions"]["typeString"]

            # Length declaration for array was None until solc 0.5.5
            if type_candidate is None:
                if expression["kind"] == "number":
                    type_candidate = "int_const"
        else:
            value = expression["attributes"].get("value", None)
            if value:
                if (
                    "subdenomination" in expression["attributes"]
                    and expression["attributes"]["subdenomination"]
                ):
                    subdenomination = expression["attributes"]["subdenomination"]
            elif value is None:
                # for literal declared as hex
                # see https://solidity.readthedocs.io/en/v0.4.25/types.html?highlight=hex#hexadecimal-literals
                assert "hexvalue" in expression["attributes"]
                value = "0x" + expression["attributes"]["hexvalue"]
            type_candidate = expression["attributes"]["type"]

        if type_candidate is None:
            if value.isdecimal():
                type_candidate = ElementaryType("uint256")
            else:
                type_candidate = ElementaryType("string")
        elif type_candidate.startswith("int_const "):
            type_candidate = ElementaryType("uint256")
        elif type_candidate.startswith("bool"):
            type_candidate = ElementaryType("bool")
        elif type_candidate.startswith("address"):
            type_candidate = ElementaryType("address")
        else:
            type_candidate = ElementaryType("string")
        literal = Literal(value, type_candidate, subdenomination)
        literal.set_offset(src, caller_context.compilation_unit)
        return literal

    if name == "Identifier":
        assert "children" not in expression

        t = None

        if caller_context.is_compact_ast:
            value = expression["name"]
            t = expression["typeDescriptions"]["typeString"]
        else:
            value = expression["attributes"]["value"]
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]

        if t:
            found = re.findall(r"[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)", t)
            assert len(found) <= 1
            if found:
                value = value + "(" + found[0] + ")"
                value = filter_name(value)

        if "referencedDeclaration" in expression:
            referenced_declaration = expression["referencedDeclaration"]
        else:
            referenced_declaration = None
        var, was_created = find_variable(value, caller_context, referenced_declaration)
        if was_created:
            var.set_offset(src, caller_context.compilation_unit)

        identifier = Identifier(var)
        identifier.set_offset(src, caller_context.compilation_unit)
        var.references.append(identifier.source_mapping)

        return identifier

    if name == "IndexAccess":
       return Expression
       pass

    if name == "MemberAccess":
       return Expression
       pass
    if name == "ElementaryTypeNameExpression":
       return Expression
       pass

    # NewExpression is not a root expression, it's always the child of another expression
    if name == "NewExpression":
        return Expression
        pass

    if name == "ModifierInvocation":
        return Expression
        pass

    if name == "IndexRangeAccess":
        return Expression
        pass

    # Introduced with solc 0.8
    if name == "IdentifierPath":
        return Expression
        pass

    raise ParsingError(f"Expression not parsed {name}")