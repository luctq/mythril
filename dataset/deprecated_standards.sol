pragma solidity 0.4.25;

contract DeprecatedSimple {
    address private owner;

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    constructor() public {
        owner = msg.sender;
    }

    // Do everything that's deprecated, then commit suicide.

    function useDeprecated() public constant onlyOwner {

        bytes32 blockhash = block.blockhash(0);
        bytes32 hashofhash = sha3(blockhash);

        uint gas = msg.gas;

        if (gas == 0) {
            throw;
        }

        address(this).callcode();

        suicide(address(0));
    }

    function () public {}

}