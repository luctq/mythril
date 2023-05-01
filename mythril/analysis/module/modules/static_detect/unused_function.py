from typing import List, Tuple
from mythril.analysis.module.base import DetectionModule, ModuleType

from mythril.solidity.ast.core.declarations.function_contract import FunctionContract
from mythril.solidity.ast.core.declarations.function import Function
from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.analysis.warning_issue import WarningIssues
class UnusedFunction(DetectionModule):
    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def _execute(self):
        issues = []

        functions_used = set()
        for contract in self.compilation_unit.contracts_derived:
            all_functionss_called = [
                f.all_internal_calls() for f in contract.functions_entry_points
            ]
            all_functions_called = [item for sublist in all_functionss_called for item in sublist]
            functions_used |= {
                f.canonical_name for f in all_functions_called if isinstance(f, Function)
            }
            all_libss_called = [f.all_library_calls() for f in contract.functions_entry_points]
            all_libs_called: List[Tuple[Contract, Function]] = [
                item for sublist in all_libss_called for item in sublist
            ]
            functions_used |= {
                lib[1].canonical_name for lib in all_libs_called if isinstance(lib, tuple)
            }
        for function in sorted(self.compilation_unit.functions, key=lambda x: x.canonical_name):
            if (
                function.visibility in ["public", "external"]
                or function.is_constructor
                or function.is_fallback
                or function.is_constructor_variables
            ):
                continue
            if function.canonical_name in functions_used:
                continue
            if isinstance(function, FunctionContract) and (
                function.contract_declarer.is_from_dependency()
            ):
                continue
            # Continue if the functon is not implemented because it means the contract is abstract
            if not function.is_implemented:
                continue
            issue = WarningIssues(
                contract=function.contract.name,
                swc_id=131,
                title="Unused Function",
                severity="Medium",
                filename=function.source_mapping.filename.short,
                description=f"Function {function.name} is never use in contract.\nRemove all unused function from the code base",
                code=function.source_mapping.code,
                lineno=function.source_mapping.get_lines_str(),
            )
            issues.append(issue)
        return issues
        