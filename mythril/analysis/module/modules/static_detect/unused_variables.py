from typing import List
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.analysis.swc_data import PRESENCE_OF_UNUSED_VARIABLES
from mythril.analysis.report import Issue
from mythril.ast.core.compilation_unit import StaticCompilationUnit
from mythril.ast.core.solidity_types.array_type import ArrayType
from mythril.ast.core.variables.state_variable import StateVariable
from mythril.analysis.warning_issue import WarningIssues
from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.cfg.node import Node
from mythril.exceptions import StaticError


def detect_unused_state_variables(contract):
    if contract.is_signature_only():
        return None
    # Get all the variables read in all the functions and modifiers
    all_functions = contract.all_functions_called + contract.modifiers
    state_variables_used = [x.state_variables_read for x in all_functions]
    state_variables_used += [
        x.state_variables_written for x in all_functions if not x.is_constructor_variables
    ]
    state_variables_used = [item for sublist in state_variables_used for item in sublist]

    # Return the variables unused that are not public
    return [x for x in contract.variables if x not in state_variables_used and x.visibility != "public"]

def detect_unused_local_variables(function):
    local_variables_used =  function.variables_read + function.variables_written
    all_local_variables = function.local_variables + function.parameters
    return [x for x in all_local_variables if x not in local_variables_used]

class UnusedVariables(DetectionModule):
    name = "Unused variable"
    swc_id = PRESENCE_OF_UNUSED_VARIABLES
    description = "Unused variable"

    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit
        
    def _execute(self) -> List[Issue]:
        """Execute detect unused state variables"""
        issues = []
        descriptions = ""
        is_issue_detected = False
        for c in self.compilation_unit.contracts_derived:
            unusedStateVars = detect_unused_state_variables(c)
            if unusedStateVars:
                is_issue_detected = True
                for var in unusedStateVars:
                    info = ["\n", var, " is never used in ", c, "\n"]
                    descriptions += "".join(self._convert_to_description(d)for d in info)
            
            for func in c.all_functions_called + c.modifiers:
                unusedLocalVars = detect_unused_local_variables(func)
                if unusedLocalVars:
                    is_issue_detected = True
                    for var in unusedLocalVars:
                        info = ["\n", var, " is never used in ", func, "\n"]
                        descriptions += "".join(self._convert_to_description(d)for d in info)
            if is_issue_detected:
                issue = WarningIssues(
                    contract=c.name,
                    swc_id=PRESENCE_OF_UNUSED_VARIABLES,
                    title="Unused Variables",
                    severity="Low",
                    filename=self.compilation_unit.core.filename,
                    descriptions=descriptions,
                )
                issues.append(issue)
        return issues

    @staticmethod
    def _convert_to_description(d):
        if isinstance(d, str):
            return d

        if not isinstance(d, SourceMapping):
            raise StaticError(f"{d} does not inherit from SourceMapping, conversion impossible")

        if isinstance(d, Node):
            if d.expression:
                return f"{d.expression} ({d.source_mapping})"
            return f"{str(d)} ({d.source_mapping})"

        if hasattr(d, "canonical_name"):
            return f"{d.canonical_name} ({d.source_mapping})"

        if hasattr(d, "name"):
            return f"{d.name} ({d.source_mapping})"

        raise StaticError(f"{type(d)} cannot be converted (no name, or canonical_name")