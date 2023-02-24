from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from mythril.ast.core.declarations.function import Function, FunctionType
from mythril.ast.core.declarations.function_contract import FunctionContract
from mythril.ast.core.variables.local_variable import LocalVariable
from mythril.ast.solc_parsing.variables.local_variable import LocalVariableSolc
if TYPE_CHECKING:
    from mythril.ast.solc_parsing.declarations.contract import ContractSolc
    from mythril.ast.core.compilation_unit import StaticCompilationUnit
    from mythril.ast.solc_parsing.static_compilation_unit_solc import StaticCompilationUnitSolc

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
        self._canonical_name: Optional[str] = None
        
        self._variables_renamed: Dict[
            int, LocalVariableSolc
        ] = {}
        self._analyze_type()

        self._local_variables_parser: List[LocalVariableSolc] = []
    
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