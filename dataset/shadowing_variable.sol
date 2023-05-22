pragma solidity 0.4.25;

contract ShadowingInFunctions {
    uint internal n = 2;
    uint internal x = 3;

    function test1() constant public returns (uint n) {
        return n; // Will return 0
    }

    function test2() constant public returns (uint n) {
        n = 1;
        return n; // Will return 1
    }

    function test3() constant public returns (uint x) {
        uint n = 4;
        return n+x; // Will return 4
    }
}