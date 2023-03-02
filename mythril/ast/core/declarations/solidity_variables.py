from typing import Dict, List
from mythril.ast.core.source_mapping.source_mapping import SourceMapping
from mythril.ast.core.solidity_types.elementary_type import ElementaryType
from mythril.exceptions import StaticException

SOLIDITY_VARIABLES = {
    "now": "uint256",
    "this": "address",
    "abi": "address",  # to simplify the conversion, assume that abi return an address
    "msg": "",
    "tx": "",
    "block": "",
    "super": "",
}

SOLIDITY_VARIABLES_COMPOSED = {
    "block.basefee": "uint",
    "block.coinbase": "address",
    "block.difficulty": "uint256",
    "block.gaslimit": "uint256",
    "block.number": "uint256",
    "block.timestamp": "uint256",
    "block.blockhash": "uint256",  # alias for blockhash. It's a call
    "block.chainid": "uint256",
    "msg.data": "bytes",
    "msg.gas": "uint256",
    "msg.sender": "address",
    "msg.sig": "bytes4",
    "msg.value": "uint256",
    "tx.gasprice": "uint256",
    "tx.origin": "address",
}

SOLIDITY_FUNCTIONS: Dict[str, List[str]] = {
    "gasleft()": ["uint256"],
    "assert(bool)": [],
    "require(bool)": [],
    "require(bool,string)": [],
    "revert()": [],
    "revert(string)": [],
    "revert ": [],
    "addmod(uint256,uint256,uint256)": ["uint256"],
    "mulmod(uint256,uint256,uint256)": ["uint256"],
    "keccak256()": ["bytes32"],
    "keccak256(bytes)": ["bytes32"],  # Solidity 0.5
    "sha256()": ["bytes32"],
    "sha256(bytes)": ["bytes32"],  # Solidity 0.5
    "sha3()": ["bytes32"],
    "ripemd160()": ["bytes32"],
    "ripemd160(bytes)": ["bytes32"],  # Solidity 0.5
    "ecrecover(bytes32,uint8,bytes32,bytes32)": ["address"],
    "selfdestruct(address)": [],
    "suicide(address)": [],
    "log0(bytes32)": [],
    "log1(bytes32,bytes32)": [],
    "log2(bytes32,bytes32,bytes32)": [],
    "log3(bytes32,bytes32,bytes32,bytes32)": [],
    "blockhash(uint256)": ["bytes32"],
    # the following need a special handling
    # as they are recognized as a SolidityVariableComposed
    # and converted to a SolidityFunction by SlithIR
    "this.balance()": ["uint256"],
    "abi.encode()": ["bytes"],
    "abi.encodePacked()": ["bytes"],
    "abi.encodeWithSelector()": ["bytes"],
    "abi.encodeWithSignature()": ["bytes"],
    "abi.encodeCall()": ["bytes"],
    "bytes.concat()": ["bytes"],
    "string.concat()": ["string"],
    # abi.decode returns an a list arbitrary types
    "abi.decode()": [],
    "type(address)": [],
    "type()": [],  # 0.6.8 changed type(address) to type()
    # The following are conversion from address.something
    "balance(address)": ["uint256"],
    "code(address)": ["bytes"],
    "codehash(address)": ["bytes32"],
}
class SolidityVariable(SourceMapping):
    def __init__(self, name: str):
        super().__init__()
        self._check_name(name)
        self._name = name

    # dev function, will be removed once the code is stable
    def _check_name(self, name: str):  # pylint: disable=no-self-use
        assert name in SOLIDITY_VARIABLES or name.endswith(("_slot", "_offset"))

    @property
    def state_variable(self):
        if self._name.endswith("_slot"):
            return self._name[:-5]
        if self._name.endswith("_offset"):
            return self._name[:-7]
        to_log = f"Incorrect YUL parsing. {self} is not a solidity variable that can be seen as a state variable"
        raise StaticException(to_log)

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> ElementaryType:
        return ElementaryType(SOLIDITY_VARIABLES[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)

class SolidityVariableComposed(SolidityVariable):
    def _check_name(self, name: str):
        assert name in SOLIDITY_VARIABLES_COMPOSED

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> ElementaryType:
        return ElementaryType(SOLIDITY_VARIABLES_COMPOSED[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)

class SolidityFunction(SourceMapping):
    pass