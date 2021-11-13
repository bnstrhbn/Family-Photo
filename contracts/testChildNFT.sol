// SPDX-License-Identifier: MIT

pragma solidity ^0.7.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract testChildNFT is ERC721 {
    uint256 public tokenCounter;
    string public tokenURI;

    constructor(string memory _tokenURI) public ERC721("CHLD", "Kid") {
        tokenCounter = 0;
        tokenURI = _tokenURI;
    }

    function createNew() public returns (uint256) {
        address owner = msg.sender;
        uint256 token_id = tokenCounter;
        _safeMint(owner, token_id);
        _setTokenURI(token_id, tokenURI);
        tokenCounter++;
        return token_id;
    }
}
