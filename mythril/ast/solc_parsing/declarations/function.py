from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from mythril.ast.core.declarations.function import Function, FunctionType
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.solc_parsing.variables.local_variable import LocalVariableSolc
from mythril.ast.solc_parsing.variables.variable_declaration import MultipleVariablesDeclaration
from mythril.ast.core.source_mapping.source_mapping import Source
from mythril.ast.core.cfg.node import NodeType, Node, link_nodes
from mythril.ast.core.cfg.scope import Scope
from mythril.ast.solc_parsing.cfg.node import NodeSolc
from mythril.ast.solc_parsing.exceptions import ParsingError
from mythril.ast.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from mythril.ast.solc_parsing.variables.local_variable_init_from_tuple import LocalVariableInitFromTupleSolc
if TYPE_CHECKING:
    from mythril.ast.solc_parsing.declarations.contract import ContractSolc
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc

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
        if self.is_compact_ast:
            self._function.name = function_data["name"]
            if "id" in function_data:
                self._function.id = function_data["id"]
        else:
            self._function.name = function_data["attributes"][self.get_key()]
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

    def _analyze_type(self):
        """
        Analyz the type of the function
        Myst be called in the constructor as the name might change according to the function's type
        For example both the fallback and the receiver will have an empty name
        :return:
        """
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed["attributes"]

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
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed["attributes"]

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
        
        if self.is_compact_ast:
            params = self._functionNotParsed["parameters"]
            returns = self._functionNotParsed["returnParameters"]
        else:
            children = self._functionNotParsed[self.get_children("children")]
            # It uses to be
            # params = children[0]
            # returns = children[1]
            # But from Solidity 0.6.3 to 0.6.10 (included)
            # Comment above a function might be added in the children
            child_iter = iter(
                [child for child in children if child[self.get_key()] == "ParameterList"]
            )
            params = next(child_iter)
            returns = next(child_iter)
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

        if self.is_compact_ast:
            body = self._functionNotParsed.get("body", None)
            if body and body[self.get_key()] == "Block":
                self._function.is_implemented = True
                self._parse_cfg(body)
            # for modifier in self._functionNotParsed["modifiers"]:
            #     self._parse_modifier(modifier)
        else:
            pass
        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self)
        for node_parser in self._node_to_nodesolc.values():
            node_parser.analyze_expressions(self)

    def _parse_cfg(self, cfg: Dict):
        assert cfg[self.get_key()] == "Block"

        node = self._new_node(NodeType.ENTRYPOINT, cfg["src"], self.underlying_function)
        self._function.entry_point = node.underlying_node

        if self.is_compact_ast:
            statements = cfg["statements"]
        else:
            statements = cfg[self.get_children("children")]
        if not statements:
            self._function.is_empty = True
        else:
            self._function.is_empty = False
            check_arithmetic = self.compilation_unit.solc_version >= "0.8.0"
            self._parse_block(cfg, node, check_arithmetic=check_arithmetic)
    def _parse_block(self, block: Dict, node: NodeSolc, check_arithmetic: bool = False):
        """
        Return:
            Node
        """
        assert block[self.get_key()] == "Block"

        if self.is_compact_ast:
            statements = block["statements"]
        else:
            statements = block[self.get_children("children")]

        check_arithmetic = check_arithmetic | node.underlying_node.scope.is_checked
        new_scope = Scope(check_arithmetic, False, node.underlying_node.scope)
        for statement in statements:
            node = self._parse_statement(statement, node, new_scope)
        return node 
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
            pass
        elif name == "WhileStatement":
            pass
        elif name == "ForStatement":
            pass
        elif name == "Block":
            pass
        elif name == "UncheckedBlock":
            pass
        elif name == "InlineAssembly":
            # Added with solc 0.6 - the yul code is an AST
            pass
        elif name == "DoWhileStatement":
            pass
        # For Continue / Break / Return / Throw
        # The is fixed later
        elif name == "Continue":
           pass
        elif name == "Break":
            pass
        elif name == "Return":
            pass
        elif name == "Throw":
            pass
        elif name == "EmitStatement":
            pass
        elif name in ["VariableDefinitionStatement", "VariableDeclarationStatement"]:
            node = self._parse_variable_definition(statement, node)
        elif name == "ExpressionStatement":
            # assert len(statement[self.get_children('expression')]) == 1
            # assert not 'attributes' in statement
            # expression = parse_expression(statement[self.get_children('children')][0], self)
            if self.is_compact_ast:
                expression = statement[self.get_children("expression")]
            else:
                expression = statement[self.get_children("expression")][0]
            new_node = self._new_node(NodeType.EXPRESSION, statement["src"], scope)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name == "TryStatement":
            pass
        # elif name == 'TryCatchClause':
        #     self._parse_catch(statement, node)
        elif name == "RevertStatement":
            pass
        else:
            raise ParsingError(f"Statement not parsed {name}")

        return node


    def _parse_params(self, params: Dict):
        assert params[self.get_key()] == "ParameterList"

        self._function.parameters_src().set_offset(params["src"], self._function.compilation_unit)
        
        if self.is_compact_ast:
            params = params["parameters"]
        else:
            params = params[self.get_children("children")]
        for param in params:
            assert param[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)
    def _parse_returns(self, returns: Dict):

        assert returns[self.get_key()] == "ParameterList"

        self._function.returns_src().set_offset(returns["src"], self._function.compilation_unit)

        if self.is_compact_ast:
            returns = returns["parameters"]
        else:
            returns = returns[self.get_children("children")]

        for ret in returns:
            assert ret[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(ret)
            self._function.add_return(local_var.underlying_variable)
    
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
           pass