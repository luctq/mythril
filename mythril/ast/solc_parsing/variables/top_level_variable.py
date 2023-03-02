from mythril.ast.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from mythril.ast.solc_parsing.declarations.caller_context import CallerContextExpression

class TopLevelVariableSolc(VariableDeclarationSolc, CallerContextExpression):
    pass