from typing import List
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.variables.state_variable import StateVariable
from mythril.solidity.ast.core.solidity_types.array_type import ArrayType
from mythril.solidity.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.analysis.warning_issue import WarningIssues

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
    OVERSHADOWED_FUNCTION = "function"
    OVERSHADOWED_MODIFIER = "modifier"
    OVERSHADOWED_STATE_VARIABLE = "state variable"
    OVERSHADOWED_EVENT = "event"

    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def detect_shadowing_definitions(self, contract):  # pylint: disable=too-many-branches
        """Detects if functions, access modifiers, events, state variables, and local variables are named after
        reserved keywords. Any such definitions are returned in a list.

        Returns:
            list of tuple: (type, contract name, definition)"""
        result = []

        # Loop through all functions + modifiers in this contract.
        for function in contract.functions + contract.modifiers:
            # We should only look for functions declared directly in this contract (not in a base contract).
            if function.contract_declarer != contract:
                continue

            # This function was declared in this contract, we check what its local variables might shadow.
            for variable in function.variables:
                overshadowed = []
                for scope_contract in [contract] + contract.inheritance:
                    # Check functions
                    for scope_function in scope_contract.functions_declared:
                        if variable.name == scope_function.name:
                            overshadowed.append((self.OVERSHADOWED_FUNCTION, scope_function))
                    # Check modifiers
                    for scope_modifier in scope_contract.modifiers_declared:
                        if variable.name == scope_modifier.name:
                            overshadowed.append((self.OVERSHADOWED_MODIFIER, scope_modifier))
                    # Check events
                    for scope_event in scope_contract.events_declared:
                        if variable.name == scope_event.name:
                            overshadowed.append((self.OVERSHADOWED_EVENT, scope_event))
                    # Check state variables
                    for scope_state_variable in scope_contract.state_variables_declared:
                        if variable.name == scope_state_variable.name:
                            overshadowed.append(
                                (self.OVERSHADOWED_STATE_VARIABLE, scope_state_variable)
                            )

                # If we have found any overshadowed objects, we'll want to add it to our result list.
                if overshadowed:
                    result.append((variable, overshadowed))

        return result

    def detect_shadowing_abstract(self, contract: Contract) -> List[List[StateVariable]]:
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

    def detect_shadowing_state(self, contract: Contract):
        ret = []
        variables_fathers = []
        for father in contract.inheritance:
            if any(f.is_implemented for f in father.functions + father.modifiers):
                variables_fathers += father.state_variables_declared

        for var in contract.state_variables_declared:
            # Ignore __gap variables for updatable contracts
            if is_upgradable_gap_variable(contract, var):
                continue

            shadow = [v for v in variables_fathers if v.name == var.name]
            if shadow:
                ret.append([var] + shadow)
        return ret
    
    def _execute(self):   
        issues = []
        # for contract in self.compilation_unit.contracts:
        #     shadowing = self.detect_shadowing_abstract(contract)
        #     if shadowing:
        #         for all_variables in shadowing:
        #             shadow = all_variables[0]
        #             variables = all_variables[1:]
        #             print(shadow, " shadows asdfasdfas:\n")

        issues = []         

        for contract in self.compilation_unit.contracts:
            shadows = self.detect_shadowing_definitions(contract)
            if shadows:
                for shadow in shadows:
                    local_variable = shadow[0]
                    overshadowed = shadow[1]
                    info = [local_variable, " shadows fgsfdg:\n"]
                    for overshadowed_entry in overshadowed:
                        (_, shadow_variable) = overshadowed_entry
                    
                    print(shadow_variable)
                    issue = WarningIssues(
                        contract= contract.name,
                        swc_id="119",
                        title="Shadowing variables",
                        severity="Medium",
                        filename=local_variable.source_mapping.filename.short,
                        description=f"Variable {local_variable} at line {local_variable.source_mapping.get_lines_str()} shadow variable {shadow_variable} at line {shadow_variable.source_mapping.get_lines_str()}. \nReview storage variable layouts for your contract systems carefully \nand remove any ambiguities. Always check for compiler warnings \nas they can flag the issue within a single contract",
                        code=local_variable.source_mapping.code.strip()+ f" (line {local_variable.source_mapping.get_lines_str()})" + '\n' + shadow_variable.source_mapping.code.strip() + f" line({shadow_variable.source_mapping.get_lines_str()})",
                        lineno=local_variable.source_mapping.get_lines_str() + f' + {shadow_variable.source_mapping.filename.short}:' + shadow_variable.source_mapping.get_lines_str(),
                    )
                    issues.append(issue);
        
        return issues;
            