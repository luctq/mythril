import re
from typing import Union, Dict, TYPE_CHECKING, List, ValuesView

from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from mythril.ast.solc_parsing.exceptions import ParsingError
from mythril.ast.core.solidity_types.elementary_type import ElementaryType, ElementaryTypeName
from mythril.ast.core.solidity_types.array_type import ArrayType
from mythril.ast.core.solidity_types.user_defined_type import UserDefinedType
from mythril.ast.core.solidity_types.function_type import FunctionType
from mythril.ast.core.solidity_types.mapping_type import MappingType
from mythril.ast.core.expressions.literal import Literal
from mythril.ast.core.variables.function_type_variable import FunctionTypeVariable


if TYPE_CHECKING:
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc
    from mythril.ast.core.declarations.structure import Structure
    from mythril.ast.core.declarations.enum import Enum
    from mythril.ast.core.declarations.contract import Contract
    from mythril.ast.core.declarations.function import Function
class UnknownType:  # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

def _find_from_type_name(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-arguments
    name: str,
    functions_direct_access: List["Function"],
    contracts_direct_access: List["Contract"],
    structures_direct_access: List["Structure"],
    all_structures: ValuesView["Structure"],
    enums_direct_access: List["Enum"],
    all_enums: ValuesView["Enum"],
) -> Type:
    name_elementary = name.split(" ")[0]
    if "[" in name_elementary:
        name_elementary = name_elementary[0 : name_elementary.find("[")]
    if name_elementary in ElementaryTypeName:
        depth = name.count("[")
        if depth:
            return ArrayType(ElementaryType(name_elementary), Literal(depth, "uint256"))
        return ElementaryType(name_elementary)
    # We first look for contract
    # To avoid collision
    # Ex: a structure with the name of a contract
    name_contract = name
    if name_contract.startswith("contract "):
        name_contract = name_contract[len("contract ") :]
    if name_contract.startswith("library "):
        name_contract = name_contract[len("library ") :]
    var_type = next((c for c in contracts_direct_access if c.name == name_contract), None)

    if not var_type:
        var_type = next((st for st in structures_direct_access if st.name == name), None)
    if not var_type:
        var_type = next((e for e in enums_direct_access if e.name == name), None)
    if not var_type:
        # any contract can refer to another contract's enum
        enum_name = name
        if enum_name.startswith("enum "):
            enum_name = enum_name[len("enum ") :]
        elif enum_name.startswith("type(enum"):
            enum_name = enum_name[len("type(enum ") : -1]
        # all_enums = [c.enums for c in contracts]
        # all_enums = [item for sublist in all_enums for item in sublist]
        var_type = next((e for e in all_enums if e.name == enum_name), None)
        if not var_type:
            var_type = next((e for e in all_enums if e.canonical_name == enum_name), None)
    if not var_type:
        # any contract can refer to another contract's structure
        name_struct = name
        if name_struct.startswith("struct "):
            name_struct = name_struct[len("struct ") :]
            name_struct = name_struct.split(" ")[0]  # remove stuff like storage pointer at the end
        # all_structures = [c.structures for c in contracts]
        # all_structures = [item for sublist in all_structures for item in sublist]
        var_type = next((st for st in all_structures if st.name == name_struct), None)
        if not var_type:
            var_type = next((st for st in all_structures if st.canonical_name == name_struct), None)
        # case where struct xxx.xx[] where not well formed in the AST
        if not var_type:
            depth = 0
            while name_struct.endswith("[]"):
                name_struct = name_struct[0:-2]
                depth += 1
            var_type = next((st for st in all_structures if st.canonical_name == name_struct), None)
            if var_type:
                return ArrayType(UserDefinedType(var_type), Literal(depth, "uint256"))

    if not var_type:
        var_type = next((f for f in functions_direct_access if f.name == name), None)
    if not var_type:
        if name.startswith("function "):
            found = re.findall(
                r"function \(([ ()\[\]a-zA-Z0-9\.,]*?)\)(?: payable)?(?: (?:external|internal|pure|view))?(?: returns \(([a-zA-Z0-9() \.,]*)\))?",
                name,
            )
            assert len(found) == 1
            params = [v for v in found[0][0].split(",") if v != ""]
            return_values = (
                [v for v in found[0][1].split(",") if v != ""] if len(found[0]) > 1 else []
            )
            params = [
                _find_from_type_name(
                    p,
                    functions_direct_access,
                    contracts_direct_access,
                    structures_direct_access,
                    all_structures,
                    enums_direct_access,
                    all_enums,
                )
                for p in params
            ]
            return_values = [
                _find_from_type_name(
                    r,
                    functions_direct_access,
                    contracts_direct_access,
                    structures_direct_access,
                    all_structures,
                    enums_direct_access,
                    all_enums,
                )
                for r in return_values
            ]
            params_vars = []
            return_vars = []
            for p in params:
                var = FunctionTypeVariable()
                var.set_type(p)
                params_vars.append(var)
            for r in return_values:
                var = FunctionTypeVariable()
                var.set_type(r)
                return_vars.append(var)
            return FunctionType(params_vars, return_vars)
    if not var_type:
        if name.startswith("mapping("):
            # nested mapping declared with var
            if name.count("mapping(") == 1:
                found = re.findall(r"mapping\(([a-zA-Z0-9\.]*) => ([ a-zA-Z0-9\.\[\]]*)\)", name)
            else:
                found = re.findall(
                    r"mapping\(([a-zA-Z0-9\.]*) => (mapping\([=> a-zA-Z0-9\.\[\]]*\))\)",
                    name,
                )
            assert len(found) == 1
            from_ = found[0][0]
            to_ = found[0][1]

            from_type = _find_from_type_name(
                from_,
                functions_direct_access,
                contracts_direct_access,
                structures_direct_access,
                all_structures,
                enums_direct_access,
                all_enums,
            )
            to_type = _find_from_type_name(
                to_,
                functions_direct_access,
                contracts_direct_access,
                structures_direct_access,
                all_structures,
                enums_direct_access,
                all_enums,
            )

            return MappingType(from_type, to_type)

    if not var_type:
        raise ParsingError("Type not found " + str(name))
    return UserDefinedType(var_type)

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
        
        structures_direct_access = contract.structures
        # structures_direct_access += contract.file_scope.structures.values()
        all_structuress = [c.structures for c in contract.file_scope.contracts.values()]
        all_structures = [item for sublist in all_structuress for item in sublist]
        # all_structures += contract.file_scope.structures.values()
        enums_direct_access: List["Enum"] = contract.enums
        # enums_direct_access += contract.file_scope.enums.values()
        all_enumss = [c.enums for c in contract.file_scope.contracts.values()]
        all_enums = [item for sublist in all_enumss for item in sublist]
        # all_enums += contract.file_scope.enums.values()

        contracts = contract.file_scope.contracts.values()
        functions = contract.functions #+ contract.modifiers
        renaming = scope.renaming
        user_defined_types = scope.user_defined_types
    elif isinstance(caller_context, StaticCompilationUnitSolc) or (
        isinstance(caller_context, FunctionSolc) and caller_context.contract_parser is None
    ):
        structures_direct_access: List["Structure"]
        if isinstance(caller_context, StaticCompilationUnitSolc):
            sl = caller_context.compilation_unit
            next_context = caller_context
            renaming = {}
            user_defined_types = sl.user_defined_value_types
        else:
            assert isinstance(caller_context, FunctionSolc)
            sl = caller_context.underlying_function.compilation_unit
            next_context = caller_context.static_parser
            renaming = caller_context.underlying_function.file_scope.renaming
            user_defined_types = caller_context.underlying_function.file_scope.user_defined_types
        structures_direct_access = sl.structures_top_level
        all_structuress = [c.structures for c in sl.contracts]
        all_structures = [item for sublist in all_structuress for item in sublist]
        all_structures += structures_direct_access
        enums_direct_access = sl.enums_top_level
        all_enumss = [c.enums for c in sl.contracts]
        all_enums = [item for sublist in all_enumss for item in sublist]
        all_enums += enums_direct_access
        contracts = sl.contracts
        functions = []
    else:
        raise ParsingError(f"Incorrect caller context: {type(caller_context)}")
    
    is_compact_ast = caller_context.is_compact_ast
    if is_compact_ast:
        key = "nodeType"
    else:
        key = "name"

    if isinstance(type_data, UnknownType):
        name = type_data.name
        if name in renaming:
            name = renaming[name]
        if name in user_defined_types:
            return user_defined_types[name]
        return _find_from_type_name(
            name,
            functions,
            contracts,
            structures_direct_access,
            all_structures,
            enums_direct_access,
            all_enums,
        )
    
    if type_data[key] == "ElementaryTypeName":
        if is_compact_ast:
            return ElementaryType(type_data["name"])
        return ElementaryType(type_data["attributes"][key])