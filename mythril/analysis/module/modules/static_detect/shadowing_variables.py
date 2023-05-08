from typing import List
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.variables.state_variable import StateVariable
from mythril.solidity.ast.core.solidity_types.array_type import ArrayType
from mythril.solidity.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.analysis.warning_issue import WarningIssues

class ShadowingVarible(DetectionModule):
    OVERSHADOWED_FUNCTION = "function"
    OVERSHADOWED_MODIFIER = "modifier"
    OVERSHADOWED_STATE_VARIABLE = "state variable"
    OVERSHADOWED_EVENT = "event"

    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def detect_shadowing_definitions(self, contract):
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
    
    def _execute(self):   
        issues = []         

        for contract in self.compilation_unit.contracts:
            shadowing_definitions = self.detect_shadowing_definitions(contract)
            if shadowing_definitions:
                for shadow in shadowing_definitions:
                    local_variable = shadow[0]
                    overshadowed = shadow[1]
                    for overshadowed_entry in overshadowed:
                        (_, shadow_variable) = overshadowed_entry

                    issue = WarningIssues(
                        contract= contract.name,
                        swc_id="119",
                        title="Shadowing variables",
                        severity="Medium",
                        filename=local_variable.source_mapping.filename.short,
                        description=f"Variable {local_variable} at line {local_variable.source_mapping.get_lines_str()} shadow variable {shadow_variable} at line {shadow_variable.source_mapping.get_lines_str()}.\n"
                        "Review storage variable layouts for your contract systems carefully and remove any ambiguities.\n"
                        "Always check for compiler warnings as they can flag the issue within a single contract",
                        code=local_variable.source_mapping.code.strip()+ f" (line {local_variable.source_mapping.get_lines_str()})" + '\n' + shadow_variable.source_mapping.code.strip() + f" line({shadow_variable.source_mapping.get_lines_str()})",
                        lineno=local_variable.source_mapping.get_lines_str() + f' + {shadow_variable.source_mapping.filename.short}:' + shadow_variable.source_mapping.get_lines_str(),
                    )
                    issues.append(issue)

        return issues
            