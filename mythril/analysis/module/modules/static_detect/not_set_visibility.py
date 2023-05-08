from typing import List, Tuple
from mythril.analysis.module.base import DetectionModule, ModuleType

from mythril.solidity.ast.core.declarations.function_contract import FunctionContract
from mythril.solidity.ast.core.declarations.function import Function
from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.analysis.warning_issue import WarningIssues

class NotSetVisibility(DetectionModule):
    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def _execute(self):
        issues = []
        for contract in self.compilation_unit.contracts_derived:
            for state_var in contract.state_variables:
                if (
                    state_var.visibility not in ["internal"]
                ):
                    continue
                if (
                    state_var.source_mapping.code.find(" internal ") != -1
                ):
                    continue
                issue = WarningIssues(
                contract=state_var.contract.name,
                swc_id=100,
                title="State variable visibility not set",
                severity="Medium",
                filename=state_var.source_mapping.filename.short,
                description=f"State variable '{state_var.name}' not set visibility.\nVariables can be specified as being public, internal or private.\nExplicitly define visibility for all state variables.",
                code=state_var.source_mapping.code.strip(),
                lineno=state_var.source_mapping.get_lines_str(),
                )
                issues.append(issue)

        for function in self.compilation_unit.functions:
            if (
                function.visibility not in ["public"]
            ):
                continue
            function_def = ''
            for line in function.source_mapping.code.split('\n'):
                function_def += line.strip() + " "
                if ("{" in line):
                    break
            if (
                function_def.find(" public ") != -1
            ):
                continue
            issue = WarningIssues(
                contract=function.contract.name,
                swc_id=100,
                title="Function visibility not set",
                severity="Medium",
                filename=function.source_mapping.filename.short,
                description=f"Function '{function.name}' not set visibility.\nFunctions can be specified as being public, internal or private.\nExplicitly define visibility for all functions",
                code=function.source_mapping.code,
                lineno=function.source_mapping.get_lines_str(),
            )
            issues.append(issue)
        return issues