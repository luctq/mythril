from typing import List
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.ast.core.compilation_unit import StaticCompilationUnit
from mythril.ast.core.declarations.contract import Contract
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.ast.core.solidity_types.array_type import ArrayType
from mythril.ast.core.solidity_types.elementary_type import ElementaryType


def is_upgradable_gap_variable(contract: Contract, variable: StateVariable) -> bool:
    """Helper function that returns true if 'variable' is a gap variable used
    for upgradable contracts. More specifically, the function returns true if:
     - variable is named "__gap"
     - it is a uint256 array declared at the end of the contract
     - it has private visibility"""

    # Return early on if the variable name is != gap to avoid iterating over all the state variables
    if variable.name != "__gap":
        return False

    declared_variable_ordered = [
        v for v in contract.state_variables_ordered if v in contract.state_variables_declared
    ]

    if not declared_variable_ordered:
        return False

    variable_type = variable.type
    return (
        declared_variable_ordered[-1] is variable
        and isinstance(variable_type, ArrayType)
        and variable_type.type == ElementaryType("uint256")
        and variable.visibility == "private"
    )

# def detect_shadowing(contract: Contract):
#     ret = []
#     variables_fathers = []
#     for father in contract.inheritance:
#         if any(f.is_implemented for f in father.functions + father.modifiers):
#             variables_fathers += father.state_variables_declared

#     for var in contract.state_variables_declared:
#         # Ignore __gap variables for updatable contracts
#         if is_upgradable_gap_variable(contract, var):
#             continue

#         shadow = [v for v in variables_fathers if v.name == var.name]
#         if shadow:
#             ret.append([var] + shadow)
#     return ret

def detect_shadowing(contract: Contract) -> List[List[StateVariable]]:
    ret: List[List[StateVariable]] = []
    variables_fathers = []
    for father in contract.inheritance:
        if all(not f.is_implemented for f in father.functions + list(father.modifiers)):
            variables_fathers += father.state_variables_declared

    var: StateVariable
    for var in contract.state_variables_declared:
        if is_upgradable_gap_variable(contract, var):
            continue

        shadow: List[StateVariable] = [v for v in variables_fathers if v.name == var.name]
        if shadow:
            ret.append([var] + shadow)
    return ret

class ShadowingVarible(DetectionModule):
    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def _execute(self):   
        issues = []
        for contract in self.compilation_unit.contracts_derived:
            shadowing = detect_shadowing(contract)
            if shadowing:
                for all_variables in shadowing:
                    print(all_variables)