import re
from typing import TYPE_CHECKING, Dict

from mythril.solidity.ast.solc_parsing.declarations.caller_context import CallerContextExpression

from mythril.solidity.ast.core.declarations.solidity_variables import SolidityVariableComposed, SOLIDITY_VARIABLES_COMPOSED
from mythril.solidity.ast.core.expressions.expression import Expression
from mythril.solidity.ast.solc_parsing.exceptions import ParsingError, VariableNotFound
from mythril.solidity.ast.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from mythril.solidity.ast.core.expressions.binary_operation import BinaryOperation, BinaryOperationType
from mythril.solidity.ast.core.expressions.conditional_expression import ConditionalExpression
from mythril.solidity.ast.core.expressions.assignment_operation import AssignmentOperation, AssignmentOperationType
from mythril.solidity.ast.core.expressions.identifier import Identifier
from mythril.solidity.ast.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from mythril.solidity.ast.core.expressions.index_acess import IndexAccess
from mythril.solidity.ast.core.expressions.type_conversion import TypeConversion
from mythril.solidity.ast.core.expressions.call_expression import CallExpression
from mythril.solidity.ast.core.expressions.member_access import MemberAccess
from mythril.solidity.ast.core.expressions.new_contract import NewContract
from mythril.solidity.ast.core.expressions.new_array import NewArray
from mythril.solidity.ast.core.expressions.new_elementary_type import NewElementaryType
from mythril.solidity.ast.core.expressions.tuple_expression import TupleExpression
from mythril.solidity.ast.core.expressions.super_identifier import SuperIdentifier
from mythril.solidity.ast.core.solidity_types.array_type import ArrayType
from mythril.solidity.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.solidity.ast.core.expressions.literal import Literal
from mythril.solidity.ast.solc_parsing.expressions.find_variable import find_variable
from mythril.solidity.ast.solc_parsing.solidity_types.type_parsing import UnknownType, parse_type
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
def parse_call(expression: Dict, caller_context):
    src = expression["src"]
    attributes = expression
    type_conversion = expression["kind"] == "typeConversion"
    type_return = attributes["typeDescriptions"]["typeString"]


    if type_conversion:
        type_call = parse_type(UnknownType(type_return), caller_context)

        assert len(expression["arguments"]) == 1
        expression_to_parse = expression["arguments"][0]

        expression = parse_expression(expression_to_parse, caller_context)
        t = TypeConversion(expression, type_call)
        t.set_offset(src, caller_context.compilation_unit)
        return t

    call_gas = None
    call_value = None
    call_salt = None

    called = parse_expression(expression["expression"], caller_context)
    # If the next expression is a FunctionCallOptions
    # We can here the gas/value information
    # This is only available if the syntax is {gas: , value: }
    # For the .gas().value(), the member are considered as function call
    # And converted later to the correct info (convert.py)
    if expression["expression"][caller_context.get_key()] == "FunctionCallOptions":
        call_with_options = expression["expression"]
        for idx, name in enumerate(call_with_options.get("names", [])):
            option = parse_expression(call_with_options["options"][idx], caller_context)
            if name == "value":
                call_value = option
            if name == "gas":
                call_gas = option
            if name == "salt":
                call_salt = option
    arguments = []
    if expression["arguments"]:
        arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
    # if isinstance(called, SuperCallExpression):
    #     sp = SuperCallExpression(called, arguments, type_return)
    #     sp.set_offset(expression["src"], caller_context.compilation_unit)
    #     return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, caller_context.compilation_unit)

    # Only available if the syntax {gas:, value:} was used
    call_expression.call_gas = call_gas
    call_expression.call_value = call_value
    call_expression.call_salt = call_salt
    return call_expression

def parse_super_name(expression: Dict, is_compact_ast: bool) -> str:
    if is_compact_ast:
        assert expression["nodeType"] == "MemberAccess"
        base_name = expression["memberName"]
        arguments = expression["typeDescriptions"]["typeString"]
    else:
        assert expression["name"] == "MemberAccess"
        attributes = expression["attributes"]
        base_name = attributes["member_name"]
        arguments = attributes["type"]

    assert arguments.startswith("function ")
    # remove function (...()
    arguments = arguments[len("function ") :]

    arguments = filter_name(arguments)
    if " " in arguments:
        arguments = arguments[: arguments.find(" ")]

    return base_name + arguments

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
        attributes = expression

        assert "prefix" in attributes

        operation_type = UnaryOperationType.get_type(attributes["operator"], attributes["prefix"])
        expression = parse_expression(expression["subExpression"], caller_context)
        unary_op = UnaryOperation(expression, operation_type)
        unary_op.set_offset(src, caller_context.compilation_unit)
        return unary_op

    if name == "BinaryOperation":
        attributes = expression
        operation_type = BinaryOperationType.get_type(attributes["operator"])

        left_expression = parse_expression(expression["leftExpression"], caller_context)
        right_expression = parse_expression(expression["rightExpression"], caller_context)

        binary_op = BinaryOperation(left_expression, right_expression, operation_type)
        binary_op.set_offset(src, caller_context.compilation_unit)
        return binary_op

    if name in "FunctionCall":
        return parse_call(expression, caller_context)

    if name == "FunctionCallOptions":
        called = parse_expression(expression["expression"], caller_context)
        assert isinstance(called, (MemberAccess, NewContract, Identifier, TupleExpression))
        return called
   
    if name == "TupleExpression":
        expressions = [
                parse_expression(e, caller_context) if e else None for e in expression["components"]
            ]
        if "attributes" in expression:
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]
                if ",," in t or "(," in t or ",)" in t:
                    t = t[len("tuple(") : -1]
                    elems = t.split(",")
                    for idx, _ in enumerate(elems):
                        if elems[idx] == "":
                            expressions.insert(idx, None)
        t = TupleExpression(expressions)
        t.set_offset(src, caller_context.compilation_unit)
        return t
    if name == "Conditional":
        if_expression = parse_expression(expression["condition"], caller_context)
        then_expression = parse_expression(expression["trueExpression"], caller_context)
        else_expression = parse_expression(expression["falseExpression"], caller_context)
    
        conditional = ConditionalExpression(if_expression, then_expression, else_expression)
        conditional.set_offset(src, caller_context.compilation_unit)
        return conditional

    if name == "Assignment":
        left_expression = parse_expression(expression["leftHandSide"], caller_context)
        right_expression = parse_expression(expression["rightHandSide"], caller_context)

        operation_type = AssignmentOperationType.get_type(expression["operator"])

        operation_return_type = expression["typeDescriptions"]["typeString"]

        assignement = AssignmentOperation(
            left_expression, right_expression, operation_type, operation_return_type
        )
        assignement.set_offset(src, caller_context.compilation_unit)
        return assignement

    if name == "Literal":
        subdenomination = None

        assert "children" not in expression

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

        value = expression["name"]
        t = expression["typeDescriptions"]["typeString"]

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
        index_type = expression["typeDescriptions"]["typeString"]
        left = expression["baseExpression"]
        right = expression.get("indexExpression", None)
        if right is None:
            ret = parse_expression(left, caller_context)
            # Nested array are not yet available in abi.decode
            if isinstance(ret, ElementaryTypeNameExpression):
                old_type = ret.type
                ret.type = ArrayType(old_type, None)
            return ret

        left_expression = parse_expression(left, caller_context)
        right_expression = parse_expression(right, caller_context)
        index = IndexAccess(left_expression, right_expression, index_type)
        index.set_offset(src, caller_context.compilation_unit)
        return index

    if name == "MemberAccess":
        
        member_name = expression["memberName"]
        member_type = expression["typeDescriptions"]["typeString"]
        # member_type = parse_type(
        #     UnknownType(expression["typeDescriptions"]["typeString"]), caller_context
        # )
        member_expression = parse_expression(expression["expression"], caller_context)
        if str(member_expression) == "super":
            super_name = parse_super_name(expression, is_compact_ast)
            var, was_created = find_variable(super_name, caller_context, is_super=True)
            if var is None:
                raise VariableNotFound(f"Variable not found: {super_name}")
            if was_created:
                var.set_offset(src, caller_context.compilation_unit)
            sup = SuperIdentifier(var)
            sup.set_offset(src, caller_context.compilation_unit)

            var.references.append(sup.source_mapping)

            return sup
        member_access = MemberAccess(member_name, member_type, member_expression)
        member_access.set_offset(src, caller_context.compilation_unit)
        if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
            id_idx = Identifier(SolidityVariableComposed(str(member_access)))
            id_idx.set_offset(src, caller_context.compilation_unit)
            return id_idx
        return member_access
    
    if name == "ElementaryTypeNameExpression":
        value = expression["typeName"]

        if isinstance(value, dict):
            t = parse_type(value, caller_context)
        else:
            t = parse_type(UnknownType(value), caller_context)
        e = ElementaryTypeNameExpression(t)
        e.set_offset(expression["src"], caller_context.compilation_unit)
        return e

    # NewExpression is not a root expression, it's always the child of another expression
    if name == "NewExpression":
        type_name = expression["typeName"]
        if type_name[caller_context.get_key()] == "ArrayTypeName":
            depth = 0
            while type_name[caller_context.get_key()] == "ArrayTypeName":
                # Note: dont conserve the size of the array if provided
                # We compute it directly
                type_name = type_name["baseType"]
                depth += 1
            if type_name[caller_context.get_key()] == "ElementaryTypeName":
                array_type = ElementaryType(type_name["name"])
            elif type_name[caller_context.get_key()] == "UserDefinedTypeName":
                if "name" not in type_name:
                    name_type = type_name["pathNode"]["name"]
                else:
                    name_type = type_name["name"]

                array_type = parse_type(UnknownType(name_type), caller_context)
            elif type_name[caller_context.get_key()] == "FunctionTypeName":
                array_type = parse_type(type_name, caller_context)
            else:
                raise ParsingError(f"Incorrect type array {type_name}")
            array = NewArray(depth, array_type)
            array.set_offset(src, caller_context.compilation_unit)
            return array
        if type_name[caller_context.get_key()] == "ElementaryTypeName":
            if is_compact_ast:
                elem_type = ElementaryType(type_name["name"])
            else:
                elem_type = ElementaryType(type_name["attributes"]["name"])
            new_elem = NewElementaryType(elem_type)
            new_elem.set_offset(src, caller_context.compilation_unit)
            return new_elem

        assert type_name[caller_context.get_key()] == "UserDefinedTypeName"

        if is_compact_ast:

            # Changed introduced in Solidity 0.8
            # see https://github.com/crytic/slither/issues/794

            # TODO explore more the changes introduced in 0.8 and the usage of pathNode/IdentifierPath
            if "name" not in type_name:
                assert "pathNode" in type_name and "name" in type_name["pathNode"]
                contract_name = type_name["pathNode"]["name"]
            else:
                contract_name = type_name["name"]
        else:
            contract_name = type_name["attributes"]["name"]
        new = NewContract(contract_name)
        new.set_offset(src, caller_context.compilation_unit)
        return new

    if name == "ModifierInvocation":
        called = parse_expression(expression["modifierName"], caller_context)
        arguments = []
        if expression.get("arguments", None):
            arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
        
        call = CallExpression(called, arguments, "Modifier")
        call.set_offset(src, caller_context.compilation_unit)
        return call

    if name == "IndexRangeAccess":
        base = parse_expression(expression["baseExpression"], caller_context)
        return base
    # Introduced with solc 0.8
    if name == "IdentifierPath":
        value = expression["name"]

        if "referencedDeclaration" in expression:
            referenced_declaration = expression["referencedDeclaration"]
        else:
            referenced_declaration = None

        var, was_created = find_variable(
            value, caller_context, referenced_declaration, is_identifier_path=True
        )
        if was_created:
            var.set_offset(src, caller_context.compilation_unit)

        identifier = Identifier(var)
        identifier.set_offset(src, caller_context.compilation_unit)

        var.references.append(identifier.source_mapping)

        return identifier

    raise ParsingError(f"Expression not parsed {name}")