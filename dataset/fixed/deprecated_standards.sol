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

        bytes32 bhash = blockhash(0);
        bytes32 hashofhash = keccak256(bhash);

        uint gas = gasleft();

        if (gas == 0) {
            revert();
        }

        address(this).delegatecall();

        selfdestruct(address(0));
    }

    function () public {}

}