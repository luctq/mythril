from mythril.exceptions import StaticException


class ParsingError(StaticException):
    pass


class VariableNotFound(StaticException):
    pass
