from typing import Dict
from mythril.ast.core.variables.variable import Variable
from mythril.ast.solc_parsing.exceptions import ParsingError

class MultipleVariablesDeclaration(Exception):
    """
    This is raised on
    var (a,b) = ...
    It should occur only on local variable definition
    """

    # pylint: disable=unnecessary-pass
    pass

class VariableDeclarationSolc:
    def __init__(
        self, variable: Variable, variable_data: Dict
    ):
        """
        A variable can be declared through a statement, or directly.
        If it is through a statement, the following children may contain
        the init value.
        It may be possible that the variable is declared through a statement,
        but the init value is declared at the VariableDeclaration children level
        """
        self._variable = variable
        self._was_analyzed = False
        self._is_compact_ast = False
        self._elem_to_parse = None
        self._initializedNotParsed = None
        self._reference_id = None

        if "nodeType" in variable_data:
            self._is_compact_ast = True
            nodeType = variable_data["nodeType"]
            if nodeType in [
                "VariableDeclarationStatement",
                "VariableDefinitionStatement",
            ]:
                if len(variable_data["declarations"]) > 1:
                    raise MultipleVariablesDeclaration
                init = None
                if "initialValue" in variable_data:
                    init = variable_data["initialValue"]
                self._init_from_declaration(variable_data["declarations"][0], init)
            elif nodeType == "VariableDeclaration":
                self._init_from_declaration(variable_data, False)
            else:
                raise ParsingError(f"Incorrect variable declaration type {nodeType}")
        else:
            pass
    
    def _init_from_declaration(self, var: Dict, init: bool):
        if self._is_compact_ast:
            attributes = var
            self._typeName = attributes["typeDescriptions"]["typeString"]
        else:
            assert len(var["children"]) <= 2
            assert var["name"] == "VariableDeclaration"

            attributes = var["attributes"]
            self._typeName = attributes["type"]
        
        self._variable.name = attributes["name"]
        if "id" in var:
            self._reference_id = var["id"]
        if "constant" in attributes:
            self._variable.is_constant = attributes["constant"]
        if "mutability" in attributes:
            # Note: this checked is not needed if "constant" was already in attribute, but we keep it
            # for completion
            if attributes["mutability"] == "constant":
                self._variable.is_constant = True
            if attributes["mutability"] == "immutable":
                self._variable.is_immutable = True
        # self._handle_comment(attributes)
        self._analyze_variable_attributes(attributes)

        if self._is_compact_ast:
            if var["typeName"]:
                self._elem_to_parse = var["typeName"]
            else:
                pass
        else:
            pass
            
        if self._is_compact_ast:
            self._initializedNotParsed = init
            if init:
                self._variable.initialized = True
        else:
            pass

    def _analyze_variable_attributes(self, attributes: Dict):
        if "visibility" in attributes:
            self._variable.visibility = attributes["visibility"]
        else:
            self._variable.visibility = "internal"