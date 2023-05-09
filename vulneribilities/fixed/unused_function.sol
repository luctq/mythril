pragma solidity 0.4.25;

contract HashForEther {
    function checkSender() private returns(bool) {
        return uint32(msg.sender) == 0;
    }

    function withdrawWinnings() public {
        // Winner if the last 8 hex characters of the address are 0.
        require(checkSender());
        _sendWinnings();
    }

    function _sendWinnings() internal{ 
        msg.sender.transfer(this.balance);
    }
}
