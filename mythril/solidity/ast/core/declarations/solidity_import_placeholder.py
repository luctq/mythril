"""
Special variable to model import with renaming
"""
from mythril.solidity.ast.core.declarations.import_directive import Import
from mythril.solidity.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.solidity.ast.core.variables.variable import Variable


class SolidityImportPlaceHolder(Variable):
    """
    Placeholder for import on top level objects
    See the example at https://blog.soliditylang.org/2020/09/02/solidity-0.7.1-release-announcement/
    In the long term we should remove this and better integrate import aliases
    """

    def __init__(self, import_directive: Import):
        super().__init__()
        assert import_directive.alias is not None
        self._import_directive = import_directive
        self._name = import_directive.alias
        self._type = ElementaryType("string")
        self._initialized = True
        self._visibility = "private"
        self._is_constant = True