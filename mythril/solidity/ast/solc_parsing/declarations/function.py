from mythril.solidity.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from mythril.solidity.ast.core.declarations.contract import Contract
from mythril.solidity.ast.core.declarations.function import Function, FunctionType, ModifierStatements
from mythril.solidity.ast.core.declarations.function_contract import FunctionContract
from mythril.solidity.ast.core.variables.local_variable import LocalVariable
from mythril.solidity.ast.solc_parsing.variables.local_variable import LocalVariableSolc
from mythril.solidity.ast.solc_parsing.variables.variable_declaration import MultipleVariablesDeclaration
from mythril.solidity.ast.core.source_mapping.source_mapping import Source
from mythril.solidity.ast.core.cfg.node import NodeType, Node, link_nodes, insert_node
from mythril.solidity.ast.core.cfg.scope import Scope
from mythril.solidity.ast.solc_parsing.cfg.node import NodeSolc
from mythril.solidity.ast.solc_parsing.exceptions import ParsingError
from mythril.solidity.ast.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from mythril.solidity.ast.solc_parsing.variables.local_variable_init_from_tuple import LocalVariableInitFromTupleSolc
from mythril.solidity.ast.solc_parsing.expressions.expression_parsing import parse_expression
from mythril.solidity.ast.astir.export_values import ExportValues

if TYPE_CHECKING:
    from mythril.solidity.ast.solc_parsing.declarations.contract import ContractSolc
    from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.solidity.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc

def link_underlying_nodes(node1: NodeSolc, node2: NodeSolc):
    link_nodes(node1.underlying_node, node2.underlying_node)
class FunctionSolc(CallerContextExpression):
    
    def __init__(
        self,
        function: Function,
        function_data: Dict,
        contract_parser: Optional["ContractSolc"],
        static_parser: "StaticCompilationUnitSolc",
    ):
        self._static_parser: "StaticCompilationUnitSolc" = static_parser
        self._contract_parser = contract_parser
        self._function = function

        # Only present if compact AST
        self._function.name = function_data["name"]
        if "id" in function_data:
            self._function.id = function_data["id"]
        self._functionNotParsed = function_data
        self._params_was_analyzed = False
        self._content_was_analyzed = False

        self._counter_scope_local_variables = 0
        # variable renamed will map the solc id
        # to the variable. It only works for compact format
        # Later if an expression provides the referencedDeclaration attr
        # we can retrieve the variable
        # It only matters if two variables have the same name in the function
        # which is only possible with solc > 0.5
        self._variables_renamed: Dict[
            int, Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]
        ] = {}

        self._analyze_type()

        self._node_to_nodesolc: Dict[Node, NodeSolc] = {}
        # self._node_to_yulobject: Dict[Node, YulBlock] = {}

        self._local_variables_parser: List[
            Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]
        ] = []

        if "documentation" in function_data:
            function.has_documentation = True
    
    @property
    def underlying_function(self) -> Function:
        return self._function

    @property
    def contract_parser(self) -> Optional["ContractSolc"]:
        return self._contract_parser

    @property
    def static_parser(self) -> "StaticCompilationUnitSolc":
        return self._static_parser

    @property
    def compilation_unit(self) -> "StaticCompilationUnit":
        return self._function.compilation_unit
    
    def get_key(self) -> str:
        return self._static_parser.get_key()

    def get_children(self, key: str) -> str:
        if self.is_compact_ast:
            return key
        return "children"

    @property
    def is_compact_ast(self):
        return self._static_parser.is_compact_ast
    
    @property
    def variables_renamed(
        self,
    ) -> Dict[int, LocalVariableSolc]:
        return self._variables_renamed

    def _add_local_variable(
        self, local_var_parser: LocalVariableSolc
    ):
        # If two local variables have the same name
        # We add a suffix to the new variable
        # This is done to prevent collision during SSA translation
        # Use of while in case of collision
        # In the worst case, the name will be really long
        # If two local variables have the same name
        # We add a suffix to the new variable
        # This is done to prevent collision during SSA translation
        # Use of while in case of collision
        # In the worst case, the name will be really long
        if local_var_parser.underlying_variable.name:
            known_variables = [v.name for v in self._function.variables]
            while local_var_parser.underlying_variable.name in known_variables:
                local_var_parser.underlying_variable.name += (
                    f"_scope_{self._counter_scope_local_variables}"
                )
                self._counter_scope_local_variables += 1
                known_variables = [v.name for v in self._function.variables]
        if local_var_parser.reference_id is not None:
            self._variables_renamed[local_var_parser.reference_id] = local_var_parser
        
        # cho nay xu ly add local variable vao function
        self._function.variables_as_dict[
            local_var_parser.underlying_variable.name
        ] = local_var_parser.underlying_variable
        self._local_variables_parser.append(local_var_parser)

    @property
    def function_not_parsed(self) -> Dict:
        return self._functionNotParsed

    def _analyze_type(self):
        """
        Analyz the type of the function
        Myst be called in the constructor as the name might change according to the function's type
        For example both the fallback and the receiver will have an empty name
        :return:
        """
        
        attributes = self._functionNotParsed

        if self._function.name == "":
            self._function.function_type = FunctionType.FALLBACK
            # 0.6.x introduced the receiver function
            # It has also an empty name, so we need to check the kind attribute
            if "kind" in attributes:
                if attributes["kind"] == "receive":
                    self._function.function_type = FunctionType.RECEIVE
        else:
            self._function.function_type = FunctionType.NORMAL

        if isinstance(self._function, FunctionContract):
            if self._function.name == self._function.contract_declarer.name:
                self._function.function_type = FunctionType.CONSTRUCTOR
    
    def _analyze_attributes(self):
        
        attributes = self._functionNotParsed

        if "payable" in attributes:
            self._function.payable = attributes["payable"]
        if "stateMutability" in attributes:
            if attributes["stateMutability"] == "payable":
                self._function.payable = True
            elif attributes["stateMutability"] == "pure":
                self._function.pure = True
                self._function.view = True
            elif attributes["stateMutability"] == "view":
                self._function.view = True

        if "constant" in attributes:
            self._function.view = attributes["constant"]

        if "isConstructor" in attributes and attributes["isConstructor"]:
            self._function.function_type = FunctionType.CONSTRUCTOR

        if "kind" in attributes:
            if attributes["kind"] == "constructor":
                self._function.function_type = FunctionType.CONSTRUCTOR

        if "visibility" in attributes:
            self._function.visibility = attributes["visibility"]
        # old solc
        elif "public" in attributes:
            if attributes["public"]:
                self._function.visibility = "public"
            else:
                self._function.visibility = "private"
        else:
            self._function.visibility = "public"

        if "payable" in attributes:
            self._function.payable = attributes["payable"]
    def _new_node(
        self, node_type: NodeType, src: Union[str, Source], scope: Union[Scope, "Function"],
        is_local_variable_declaration = False
    ) -> NodeSolc:
        node = self._function.new_node(node_type, src, scope)
        node.is_local_variable_declaration = is_local_variable_declaration
        node_parser = NodeSolc(node)
        self._node_to_nodesolc[node] = node_parser
        return node_parser

    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return
        self._params_was_analyzed = True
        self._analyze_attributes()
        
        params = self._functionNotParsed["parameters"]
        returns = self._functionNotParsed["returnParameters"]

        if params:
            self._parse_params(params)
        if returns:
            self._parse_returns(returns)

    def _add_param(self, param: Dict) -> LocalVariableSolc:

        local_var = LocalVariable()
        local_var.set_function(self._function)
        local_var.set_offset(param["src"], self._function.compilation_unit)

        local_var_parser = LocalVariableSolc(local_var, param)
        
        local_var_parser.analyze(self)
        # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        if local_var.location == "default":
            local_var.set_location("memory")

        self._add_local_variable(local_var_parser)
        return local_var_parser
    
    def analyze_content(self):
        if self._content_was_analyzed:
            return
        self._content_was_analyzed = True

        body = self._functionNotParsed.get("body", None)
        if body and body[self.get_key()] == "Block":
            self._function.is_implemented = True
            self._parse_cfg(body)
        for modifier in self._functionNotParsed["modifiers"]:
            self._parse_modifier(modifier)

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self)
        for node_parser in self._node_to_nodesolc.values():
            node_parser.analyze_expressions(self)

    def _parse_cfg(self, cfg: Dict):
        assert cfg[self.get_key()] == "Block"

        node = self._new_node(NodeType.ENTRYPOINT, cfg["src"], self.underlying_function)
        self._function.entry_point = node.underlying_node

        statements = cfg["statements"]
        if not statements:
            self._function.is_empty = True
        else:
            self._function.is_empty = False
            check_arithmetic = self.compilation_unit.solc_version >= "0.8.0"
            self._parse_block(cfg, node, check_arithmetic=check_arithmetic)
    
    def _parse_modifier(self, modifier: Dict):
        # [{'id': 34, 'kind': 'modifierInvocation', 'modifierName': {'id': 33, 'name': 'requireB', 'nameLocations': ['303:8:0'], 'nodeType': 'IdentifierPath', 'referencedDeclaration': 31, 'src': '303:8:0'}, 'nodeType': 'ModifierInvocation', 'src': '303:8:0'}]
        m = parse_expression(modifier, self)
        # self._expression_modifiers.append(m)

        # Do not parse modifier nodes for interfaces
        if not self._function.is_implemented:
            return

        for m in ExportValues(m).result():
            if isinstance(m, Function):
                node_parser = self._new_node(
                    NodeType.EXPRESSION, modifier["src"], self.underlying_function
                )
                node_parser.add_unparsed_expression(modifier)
                # The latest entry point is the entry point, or the latest modifier call
                if self._function.modifiers:
                    latest_entry_point = self._function.modifiers_statements[-1].nodes[-1]
                else:
                    latest_entry_point = self._function.entry_point
                insert_node(latest_entry_point, node_parser.underlying_node)
                self._function.add_modifier(
                    ModifierStatements(
                        modifier=m,
                        entry_point=latest_entry_point,
                        nodes=[latest_entry_point, node_parser.underlying_node],
                    )
                )

            elif isinstance(m, Contract):
                node_parser = self._new_node(
                    NodeType.EXPRESSION, modifier["src"], self.underlying_function
                )
                node_parser.add_unparsed_expression(modifier)
                # The latest entry point is the entry point, or the latest constructor call
                if self._function.explicit_base_constructor_calls_statements:
                    latest_entry_point = self._function.explicit_base_constructor_calls_statements[
                        -1
                    ].nodes[-1]
                else:
                    latest_entry_point = self._function.entry_point
                insert_node(latest_entry_point, node_parser.underlying_node)
                self._function.add_explicit_base_constructor_calls_statements(
                    ModifierStatements(
                        modifier=m,
                        entry_point=latest_entry_point,
                        nodes=[latest_entry_point, node_parser.underlying_node],
                    )
                )

    def _parse_block(self, block: Dict, node: NodeSolc, check_arithmetic: bool = False):
        """
        Return:
            Node
        """
        assert block[self.get_key()] == "Block"
        statements = block["statements"]

        check_arithmetic = check_arithmetic | node.underlying_node.scope.is_checked
        new_scope = Scope(check_arithmetic, False, node.underlying_node.scope)
        for statement in statements:
            node = self._parse_statement(statement, node, new_scope)
        return node 
    
    def _parse_unchecked_block(self, block: Dict, node: NodeSolc):
        """
        Return:
            Node
        """
        assert block[self.get_key()] == "UncheckedBlock"

        statements = block["statements"]

        new_scope = Scope(False, False, node.underlying_node.scope)
        for statement in statements:
            node = self._parse_statement(statement, node, new_scope)
        return node

    def _parse_if(self, if_statement: Dict, node: NodeSolc) -> NodeSolc:
        falseStatement = None
        
        condition = if_statement["condition"]
        # Note: check if the expression could be directly
        # parsed here 
        condition_node = self._new_node(
            NodeType.IF, condition["src"], node.underlying_node.scope
        )
        condition_node.add_unparsed_expression(condition)
        link_underlying_nodes(node, condition_node)
        true_scope = Scope(
            node.underlying_node.scope.is_checked, False, node.underlying_node.scope
        )
        trueStatement = self._parse_statement(
            if_statement["trueBody"], condition_node, true_scope
        )
        if "falseBody" in if_statement and if_statement["falseBody"]:
            false_scope = Scope(
                node.underlying_node.scope.is_checked, False, node.underlying_node.scope
            )
            falseStatement = self._parse_statement(
                if_statement["falseBody"], condition_node, false_scope
            )

        endIf_node = self._new_node(NodeType.ENDIF, if_statement["src"], node.underlying_node.scope)
        link_underlying_nodes(trueStatement, endIf_node)

        if falseStatement:
            link_underlying_nodes(falseStatement, endIf_node)
        else:
            link_underlying_nodes(condition_node, endIf_node)
        return endIf_node

    def _parse_while(self, whilte_statement: Dict, node: NodeSolc) -> NodeSolc:
        # WhileStatement = 'while' '(' Expression ')' Statement

        node_startWhile = self._new_node(
            NodeType.STARTLOOP, whilte_statement["src"], node.underlying_node.scope
        )

        body_scope = Scope(node.underlying_node.scope.is_checked, False, node.underlying_node.scope)

        node_condition = self._new_node(
                NodeType.IFLOOP, whilte_statement["condition"]["src"], node.underlying_node.scope
            )
        node_condition.add_unparsed_expression(whilte_statement["condition"])
        statement = self._parse_statement(whilte_statement["body"], node_condition, body_scope)

        node_endWhile = self._new_node(
            NodeType.ENDLOOP, whilte_statement["src"], node.underlying_node.scope
        )

        link_underlying_nodes(node, node_startWhile)
        link_underlying_nodes(node_startWhile, node_condition)
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        # ForStatement = 'for' '(' (SimpleStatement)? ';' (Expression)? ';' (ExpressionStatement)? ')' Statement
        
        body = statement["body"]
        pre = statement.get("initializationExpression", None)
        cond = statement.get("condition", None)
        post = statement.get("loopExpression", None)

        node_startLoop = self._new_node(
            NodeType.STARTLOOP, statement["src"], node.underlying_node.scope
        )
        node_endLoop = self._new_node(
            NodeType.ENDLOOP, statement["src"], node.underlying_node.scope
        )

        last_scope = node.underlying_node.scope

        if pre:
            pre_scope = Scope(node.underlying_node.scope.is_checked, False, last_scope)
            last_scope = pre_scope
            node_init_expression = self._parse_statement(pre, node, pre_scope)
            link_underlying_nodes(node_init_expression, node_startLoop)
        else:
            link_underlying_nodes(node, node_startLoop)

        if cond:
            cond_scope = Scope(node.underlying_node.scope.is_checked, False, last_scope)
            last_scope = cond_scope
            node_condition = self._new_node(NodeType.IFLOOP, cond["src"], cond_scope)
            node_condition.add_unparsed_expression(cond)
            link_underlying_nodes(node_startLoop, node_condition)

            node_beforeBody = node_condition
        else:
            node_condition = None
            node_beforeBody = node_startLoop

        body_scope = Scope(node.underlying_node.scope.is_checked, False, last_scope)
        last_scope = body_scope
        node_body = self._parse_statement(body, node_beforeBody, body_scope)

        if post:
            node_loopexpression = self._parse_statement(post, node_body, last_scope)
            link_underlying_nodes(node_loopexpression, node_beforeBody)
        else:
            # node_loopexpression = None
            link_underlying_nodes(node_body, node_beforeBody)

        if node_condition:
            link_underlying_nodes(node_condition, node_endLoop)
        else:
            link_underlying_nodes(
                node_startLoop, node_endLoop
            )  # this is an infinite loop but we can't break our cfg

        return node_endLoop
    
    def _parse_dowhile(self, do_while_statement: Dict, node: NodeSolc) -> NodeSolc:

        node_startDoWhile = self._new_node(
            NodeType.STARTLOOP, do_while_statement["src"], node.underlying_node.scope
        )
        condition_scope = Scope(
            node.underlying_node.scope.is_checked, False, node.underlying_node.scope
        )

        node_condition = self._new_node(
            NodeType.IFLOOP, do_while_statement["condition"]["src"], condition_scope
        )
        node_condition.add_unparsed_expression(do_while_statement["condition"])
        statement = self._parse_statement(
            do_while_statement["body"], node_condition, condition_scope
        )

        body_scope = Scope(node.underlying_node.scope.is_checked, False, condition_scope)
        node_endDoWhile = self._new_node(NodeType.ENDLOOP, do_while_statement["src"], body_scope)

        link_underlying_nodes(node, node_startDoWhile)
        # empty block, loop from the start to the condition
        if not node_condition.underlying_node.sons:
            link_underlying_nodes(node_startDoWhile, node_condition)
        else:
            link_nodes(
                node_startDoWhile.underlying_node,
                node_condition.underlying_node.sons[0],
            )
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endDoWhile)
        return node_endDoWhile

    def _parse_try_catch(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        # Lay ra thong tin thuoc tinh externalCall neu khong co tra ve
        externalCall = statement.get("externalCall", None)

        if externalCall is None:
            raise ParsingError(f"Try/Catch not correctly parsed by Slither {statement}")
        catch_scope = Scope(
            node.underlying_node.scope.is_checked, False, node.underlying_node.scope
        )
        new_node = self._new_node(NodeType.TRY, statement["src"], catch_scope)
        new_node.add_unparsed_expression(externalCall)
        link_underlying_nodes(node, new_node)
        node = new_node

        for clause in statement.get("clauses", []):
            self._parse_catch(clause, node)
        return node

    def _parse_catch(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        block = statement.get("block", None)

        if block is None:
            raise ParsingError(f"Catch not correctly parsed by Slither {statement}")
        try_scope = Scope(node.underlying_node.scope.is_checked, False, node.underlying_node.scope)

        try_node = self._new_node(NodeType.CATCH, statement["src"], try_scope)
        link_underlying_nodes(node, try_node)

        params = statement.get("parameters", None)

        if params:
            for param in params.get("parameters", []):
                assert param[self.get_key()] == "VariableDeclaration"
                self._add_param(param)

        return self._parse_statement(block, try_node, try_scope)

    def _parse_statement(
        self, statement: Dict, node: NodeSolc, scope: Union[Scope, Function]
    ) -> NodeSolc:
        """

        Return:
            node
        """
        # Statement = IfStatement | WhileStatement | ForStatement | Block | InlineAssemblyStatement |
        #            ( DoWhileStatement | PlaceholderStatement | Continue | Break | Return |
        #                          Throw | EmitStatement | SimpleStatement ) ';'
        # SimpleStatement = VariableDefinition | ExpressionStatement

        name = statement[self.get_key()]
        # SimpleStatement = VariableDefinition | ExpressionStatement
        if name == "IfStatement":
            node = self._parse_if(statement, node)
        elif name == "WhileStatement":
            node = self._parse_while(statement, node)
        elif name == "ForStatement":
            node = self._parse_for(statement, node)
        elif name == "Block":
            node = self._parse_block(statement, node)
        elif name == "UncheckedBlock":
            node = self._parse_unchecked_block(statement, node)
        elif name == "InlineAssembly":
            # Added with solc 0.6 - the yul code is an AST
            pass
        elif name == "DoWhileStatement":
            node = self._parse_dowhile(statement, node)
        # For Continue / Break / Return / Throw
        # The is fixed later
        elif name == "Continue":
            continue_node = self._new_node(NodeType.CONTINUE, statement["src"], scope)
            link_underlying_nodes(node, continue_node)
            node = continue_node
        elif name == "Break":
            break_node = self._new_node(NodeType.BREAK, statement["src"], scope)
            link_underlying_nodes(node, break_node)
            node = break_node
        elif name == "Return":
            return_node = self._new_node(NodeType.RETURN, statement["src"], scope)
            link_underlying_nodes(node, return_node)
            if statement.get("expression", None):
                return_node.add_unparsed_expression(statement["expression"])
            node = return_node
        elif name == "Throw":
            throw_node = self._new_node(NodeType.THROW, statement["src"], scope)
            link_underlying_nodes(node, throw_node)
            node = throw_node
        elif name == "EmitStatement":
            expression = statement["eventCall"]

            new_node = self._new_node(NodeType.EXPRESSION, statement["src"], scope)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name in ["VariableDefinitionStatement", "VariableDeclarationStatement"]:
            node = self._parse_variable_definition(statement, node)
        elif name == "ExpressionStatement":
            # assert len(statement[self.get_children('expression')]) == 1
            # assert not 'attributes' in statement
            # expression = parse_expression(statement[self.get_children('children')][0], self)
            expression = statement[self.get_children("expression")]
            new_node = self._new_node(NodeType.EXPRESSION, statement["src"], scope)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name == "TryStatement":
            node = self._parse_try_catch(statement, node)
        # elif name == 'TryCatchClause':
        #     self._parse_catch(statement, node)
        elif name == "RevertStatement":
            expression = statement[self.get_children("errorCall")]
            new_node = self._new_node(NodeType.EXPRESSION, statement["src"], scope)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        else:
            raise ParsingError(f"Statement not parsed {name}")

        return node

    
    def _parse_params(self, params: Dict):
        assert params[self.get_key()] == "ParameterList"

        self._function.parameters_src().set_offset(params["src"], self._function.compilation_unit)
 
        params = params["parameters"]
        for param in params:
            assert param[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)
    def _parse_returns(self, returns: Dict):

        assert returns[self.get_key()] == "ParameterList"

        self._function.returns_src().set_offset(returns["src"], self._function.compilation_unit)

        returns = returns["parameters"]

        for ret in returns:
            assert ret[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(ret)
            self._function.add_return(local_var.underlying_variable)
    def _parse_variable_definition_init_tuple(
        self, statement: Dict, index: int, node: NodeSolc
    ) -> NodeSolc:
        local_var = LocalVariableInitFromTuple()
        local_var.set_function(self._function)
        local_var.set_offset(statement["src"], self._function.compilation_unit)

        local_var_parser = LocalVariableInitFromTupleSolc(local_var, statement, index)

        self._add_local_variable(local_var_parser)

        new_node = self._new_node(NodeType.VARIABLE, statement["src"], node.underlying_node.scope)
        new_node.underlying_node.add_variable_declaration(local_var)
        link_underlying_nodes(node, new_node)
        return new_node
    
    def _parse_variable_definition(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        try:
            local_var = LocalVariable()
            local_var.set_function(self._function)
            local_var.set_offset(statement["src"], self._function.compilation_unit)

            local_var_parser = LocalVariableSolc(local_var, statement)
            self._add_local_variable(local_var_parser)
            # local_var.analyze(self)

            new_node = self._new_node(
                NodeType.VARIABLE, statement["src"], node.underlying_node.scope,
                is_local_variable_declaration=True
            )
            new_node.underlying_node.add_variable_declaration(local_var)
            link_underlying_nodes(node, new_node)
            return new_node
        except MultipleVariablesDeclaration:
           # Custom handling of var (a,b) = .. style declaration
            variables = statement["declarations"]
            count = len(variables)

            if (
                statement["initialValue"]["nodeType"] == "TupleExpression"
                and len(statement["initialValue"]["components"]) == count
            ):
                inits = statement["initialValue"]["components"]
                i = 0
                new_node = node
                for variable in variables:
                    if variable is None:
                        continue
                    init = inits[i]
                    src = variable["src"]
                    i = i + 1

                    new_statement = {
                        "nodeType": "VariableDefinitionStatement",
                        "src": src,
                        "declarations": [variable],
                        "initialValue": init,
                    }
                    new_node = self._parse_variable_definition(new_statement, new_node)

            else:
                # If we have
                # var (a, b) = f()
                # we can split in multiple declarations, without init
                # Then we craft one expression that does the assignment
                variables = []
                i = 0
                new_node = node
                for variable in statement["declarations"]:
                    if variable:
                        src = variable["src"]
                        # Create a fake statement to be consistent
                        new_statement = {
                            "nodeType": "VariableDefinitionStatement",
                            "src": src,
                            "declarations": [variable],
                        }
                        variables.append(variable)

                        new_node = self._parse_variable_definition_init_tuple(
                            new_statement, i, new_node
                        )
                    i = i + 1

                var_identifiers = []
                # craft of the expression doing the assignement
                for v in variables:
                    identifier = {
                        "nodeType": "Identifier",
                        "src": v["src"],
                        "name": v["name"],
                        "typeDescriptions": {"typeString": v["typeDescriptions"]["typeString"]},
                    }
                    var_identifiers.append(identifier)

                tuple_expression = {
                    "nodeType": "TupleExpression",
                    "src": statement["src"],
                    "components": var_identifiers,
                }

                expression = {
                    "nodeType": "Assignment",
                    "src": statement["src"],
                    "operator": "=",
                    "type": "tuple()",
                    "leftHandSide": tuple_expression,
                    "rightHandSide": statement["initialValue"],
                    "typeDescriptions": {"typeString": "tuple()"},
                }
                node = new_node
                new_node = self._new_node(
                    NodeType.EXPRESSION, statement["src"], node.underlying_node.scope
                )
                new_node.add_unparsed_expression(expression)
                link_underlying_nodes(node, new_node)

            return new_node