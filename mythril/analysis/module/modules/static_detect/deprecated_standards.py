from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit

from mythril.solidity.ast.core.declarations.solidity_variables import SolidityFunction, SolidityVariableComposed
from mythril.solidity.ast.core.cfg.node import NodeType
from mythril.solidity.ast.astir.operations.low_level_call import LowLevelCall
from mythril.solidity.ast.astir.export_values import ExportValues
from mythril.analysis.warning_issue import WarningIssues
class DeprecatedStandards(DetectionModule):
    """
    Use of Deprecated Standards
    """
    DEPRECATED_SOLIDITY_VARIABLE = [
        ("block.blockhash", "block.blockhash()", "blockhash()"),
        ("msg.gas", "msg.gas", "gasleft()"),
    ]
    DEPRECATED_SOLIDITY_FUNCTIONS = [
        ("suicide(address)", "suicide()", "selfdestruct()"),
        ("sha3()", "sha3()", "keccak256()"),
    ]
    DEPRECATED_NODE_TYPES = [(NodeType.THROW, "throw", "revert()")]
    DEPRECATED_LOW_LEVEL_CALLS = [("callcode", "callcode", "delegatecall")]

    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def detect_deprecation_in_expression(self, expression):
        """Detects if an expression makes use of any deprecated standards.

        Returns:
            list of tuple: (detecting_signature, original_text, recommended_text)"""
        
        export = ExportValues(expression)
        export_values = export.result()

        # Define our results list
        results = []

        # Check if there is usage of any deprecated solidity variables or functions
        for dep_var in self.DEPRECATED_SOLIDITY_VARIABLE:
            if SolidityVariableComposed(dep_var[0]) in export_values:
                results.append(dep_var)
        for dep_func in self.DEPRECATED_SOLIDITY_FUNCTIONS:
            if SolidityFunction(dep_func[0]) in export_values:
                results.append(dep_func)

        return results

    def detect_deprecated_references_in_node(self, node):
        """Detects if a node makes use of any deprecated standards.

        Returns:
            list of tuple: (detecting_signature, original_text, recommended_text)"""
        # Define our results list
        results = []

        # If this node has an expression, we check the underlying expression.
        if node.expression:
            results += self.detect_deprecation_in_expression(node.expression)

        # Check if there is usage of any deprecated solidity variables or functions
        for dep_node in self.DEPRECATED_NODE_TYPES:
            if node.type == dep_node[0]:
                results.append(dep_node)

        return results

    def detect_deprecated_references_in_contract(self, contract):
        """Detects the usage of any deprecated built-in symbols.

        Returns:
            list of tuple: (state_variable | node, (detecting_signature, original_text, recommended_text))"""
        results = []

        for state_variable in contract.state_variables_declared:
            if state_variable.expression:
                deprecated_results = self.detect_deprecation_in_expression(
                    state_variable.expression
                )
                if deprecated_results:
                    results.append((state_variable, deprecated_results))

        # Loop through all functions + modifiers in this contract.
        for function in contract.functions_and_modifiers_declared:
            # Loop through each node in this function.
            for node in function.nodes:
                # Detect deprecated references in the node.
                deprecated_results = self.detect_deprecated_references_in_node(node)

                # Detect additional deprecated low-level-calls.
                for ir in node.irs:
                    if isinstance(ir, LowLevelCall):
                        for dep_llc in self.DEPRECATED_LOW_LEVEL_CALLS:
                            if ir.function_name == dep_llc[0]:
                                deprecated_results.append(dep_llc)

                # If we have any results from this iteration, add them to our results list.
                if deprecated_results:
                    results.append((node, deprecated_results))

        return results

    def _execute(self):
        """Detects if an expression makes use of any deprecated standards.

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'deprecated_references'}

        """
        issues = []
        for contract in self.compilation_unit.contracts:
            deprecated_references = self.detect_deprecated_references_in_contract(contract)
            if deprecated_references:
                for deprecated_reference in deprecated_references:
                    source_object = deprecated_reference[0]
                    deprecated_entries = deprecated_reference[1]
                    (_, original_desc, recommended_disc) = deprecated_entries[0]
                    issue = WarningIssues(
                        contract=contract.name,
                        swc_id="111",
                        title="Use of Deprecated solidity function",
                        severity="Medium",
                        filename=source_object.source_mapping.filename.short,
                        description=f'Usage of "{original_desc}" should be replaced with "{recommended_disc}". \nSeveral functions and operators in Solidity are deprecated. \nUsing them leads to reduced code quality. \nWith new major versions of the Solidity compiler, \ndeprecated functions and operators may result in side effects and compile errors.',
                        code=source_object.source_mapping.code.strip(),
                        lineno= source_object.source_mapping.get_lines_str(),
                    )
                    issues.append(issue)
            
        return issues