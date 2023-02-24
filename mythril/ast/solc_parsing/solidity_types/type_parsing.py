from typing import Union, Dict, TYPE_CHECKING

from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.solc_parsing.exceptions import ParsingError
from mythril.ast.core.solidity_types.elementary_type import ElementaryType
if TYPE_CHECKING:
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc

class UnknownType:  # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

def parse_type(
    type_data: Union[Dict, UnknownType],
    caller_context: Union[CallerContextExpression, "StaticCompilationUnitSolc"],
) -> Type:
    # local import to avoid circular dependency
    from mythril.ast.solc_parsing.declarations.contract import ContractSolc
    from mythril.ast.solc_parsing.declarations.function import FunctionSolc
    if isinstance(caller_context, (ContractSolc, FunctionSolc)):
        if isinstance(caller_context, FunctionSolc):
            underlying_func = caller_context.underlying_function
            # If contract_parser is set to None, then underlying_function is a functionContract
            # See note above
            assert isinstance(underlying_func, FunctionContract)
            contract = underlying_func.contract
            next_context = caller_context.contract_parser
            scope = caller_context.underlying_function.file_scope
        else:
            contract = caller_context.underlying_contract
            next_context = caller_context
            scope = caller_context.underlying_contract.file_scope
        
        contracts = contract.file_scope.contracts.values()
        functions = contract.functions #+ contract.modifiers
        renaming = scope.renaming
        user_defined_types = scope.user_defined_types
    else:
        raise ParsingError(f"Incorrect caller context: {type(caller_context)}")
    
    is_compact_ast = caller_context.is_compact_ast
    if is_compact_ast:
        key = "nodeType"
    else:
        key = "name"
    if type_data[key] == "ElementaryTypeName":
        if is_compact_ast:
            return ElementaryType(type_data["name"])
        return ElementaryType(type_data["attributes"][key])