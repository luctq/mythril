from mythril.ast.core.expressions.expression import Expression


class NewContract(Expression):
    def __init__(self, contract_name):
        super().__init__()
        self._contract_name: str = contract_name
        self._gas = None
        self._value = None
        self._salt = None
