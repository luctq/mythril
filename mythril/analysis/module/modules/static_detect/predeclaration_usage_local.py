from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.ast.core.compilation_unit import StaticCompilationUnit

class PredeclarationUsageLocal(DetectionModule):
    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def detect_predeclared_local_usage(self, node, results, already_declared, visited):
        """
        Detects if a given node uses a variable prior to declaration in any code path.
        :param node: The node to initiate the scan from (searches recursively through all sons)
        :param already_declared: A set of variables already known to be declared in this path currently.
        :param already_visited: A set of nodes already visited in this path currently.
        :param results: A list of tuple(node, local_variable) denoting nodes which used a variable before declaration.
        :return: None
        """

        if node in visited:
            return

        visited = visited | {node}

        if node.variable_declaration:
            already_declared = already_declared | {node.variable_declaration}

        if not node in self.fix_point_information:
            self.fix_point_information[node] = []

        # If we already explored this node with the same information
        if already_declared:
            for fix_point in self.fix_point_information[node]:
                if fix_point == already_declared:
                    return

        if already_declared:
            self.fix_point_information[node] += [already_declared]

        for variable in set(node.local_variables_read + node.local_variables_written):
            if variable not in already_declared:
                result = (node, variable)
                if result not in results:
                    results.append(result)

        for son in node.sons:
            self.detect_predeclared_local_usage(son, results, already_declared, visited)
        
    def detect_predeclared_in_contract(self, contract):
        """
        Detects and returns all nodes in a contract which use a variable before it is declared.
        :param contract: Contract to detect pre-declaration usage of locals within.
        :return: A list of tuples: (function, list(tuple(node, local_variable)))
        """

        # Create our result set.
        results = []

        # Loop for each function and modifier's nodes and analyze for predeclared local variable usage.
        for function in contract.functions_and_modifiers_declared:
            predeclared_usage = []
            if function.nodes:
                self.detect_predeclared_local_usage(
                    function.nodes[0],
                    predeclared_usage,
                    set(function.parameters + function.returns),
                    set(),
                )
            if predeclared_usage:
                results.append((function, predeclared_usage))

        # Return the resulting set of nodes which set array length.
        return results
    
    def _execute(self):
        """
        Detect usage of a local variable before it is declared.
        """
        results = []

        # Fix_point_information contains a list of set
        # Each set contains the already declared variables saw in one path
        # If a path has the same set as a path already explored
        # We don't need to continue
        # pylint: disable=attribute-defined-outside-init
        self.fix_point_information = {}

        for contract in self.compilation_unit.contracts:
            predeclared_usages = self.detect_predeclared_in_contract(contract)
            if predeclared_usages:
                for (predeclared_usage_function, predeclared_usage_nodes) in predeclared_usages:
                    for (
                        predeclared_usage_node,
                        predeclared_usage_local_variable,
                    ) in predeclared_usage_nodes:
                        info = [
                            "Variable '",
                            predeclared_usage_local_variable,
                            "' in ",
                            predeclared_usage_function,
                            " potentially used before declaration: ",
                            predeclared_usage_node,
                            "\n",
                        ]

                        print("Variable '",
                            predeclared_usage_local_variable,
                            "' in ",
                            predeclared_usage_function,
                            " potentially used before declaration: ",
                            predeclared_usage_node,
                            "\n")