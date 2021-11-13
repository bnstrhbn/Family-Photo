//SPDX-License-Identifier:MIT
pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2; //got this from Linkpool's keeper job on mainnet - for use with abi encode/decode any my uint256[][] 
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@chainlink/contracts/src/v0.7/ChainlinkClient.sol";

contract ParentNFT is ERC721, ChainlinkClient {
    using Chainlink for Chainlink.Request;
    //CL EA setup
    bytes32 private jobId;
    uint256 private fee;

    //for use with testing keeper job and the commented out functions at the bottom
    //bool public upkeepvar;
    //uint256[][] public tokensToWorkvar; 
    
    mapping(bytes32 => uint256) public requestIdToParentTokenID; //for use with EA callback
    string public latestTokenURI; //see the result of the latest EA callback - used for testing

    uint256 public tokenCounter; //total count of NFTs minted by Family Photo
    struct ChildNFT { //holds the information about NFTs users added to a Family Photo
        address owner;
        address childAddress;
        uint256 childTokenId;
    }

    mapping(uint256 => ChildNFT[]) public tokenMapping; //Family Photo tokenID -> nfts that were added to it by users
    mapping(uint256 => uint256) public childTokenCount; //Family Photo tokenID -> totalnum child tokens in that token
    mapping(uint256 => mapping(uint256 => bool)) public activeMapping; //ptokenID => childToken(struct)ID => active. took out of the struct for ease of use
    mapping(uint256 => uint8) public tokenStatusMap; //parent token id -> minting status of that token need to case enum as uint8() in the mapping

    event RequestFulfilled(bytes32 indexed requestId, bytes indexed data);
    event finalizeParentNFT(address requester); 
    event tokenAdded(uint256 indexed tokenId);

    enum TOKEN_STATUS {
        OPEN,
        IN_PROGRESS,
        FINAL
    }

    constructor() public ERC721("FAM", "Family Photo") {
        setChainlinkToken(0xa36085F69e2889c224210F603D836748e7dC0088);
        tokenCounter = 0;
        setChainlinkOracle(0x0EBc28BE8687373DF8Fb4AB353f351Ab19694681); //my node on kovan
        jobId = "34eb419a6300406694c9565d1d846212"; //my EA job
        fee = 1 * 10**18; // 1 LINK
    }

    function makeNewGroup() public returns (uint256) {
        //begin new minting - can have multiple open and people add to open ones.
        uint256 parentTokenId = tokenCounter;
        tokenStatusMap[parentTokenId] = uint8(TOKEN_STATUS.OPEN); //need to case enum as uint8() in the mapping
        address owner = msg.sender;
        _safeMint(owner, parentTokenId);
        tokenStatusMap[parentTokenId] = uint8(TOKEN_STATUS.OPEN);
        childTokenCount[parentTokenId] = 0;
        tokenCounter = tokenCounter + 1;
        return parentTokenId;
    }

    function addMyToken(
        uint256 parentTokenId,
        address childTokenAddress,
        uint256 childTokenId
    ) public returns (bool) {
        //function to add a token to the list. ie big array - parent token id => address|tokenid
        //could have multiple users or multiple types of tokens/ids. concat token address|tokenid
        //set property = active for this child token too.
        uint8 tokenState = tokenStatusMap[parentTokenId];
        require(
            parentTokenId < tokenCounter,
            "This parent token doens't exist yet"
        );
        require(
            tokenState != uint8(TOKEN_STATUS.FINAL),
            "Token is not available to add new data"
        );
        tokenStatusMap[parentTokenId] = uint8(TOKEN_STATUS.IN_PROGRESS); //need to case enum as uint8() in the mapping
        //add pointer to child NFT
        //given childTokenAddress, instantiate an object of that contract type
        ERC721 child_nft = ERC721(childTokenAddress);
        //check owner
        require(
            msg.sender == child_nft.ownerOf(childTokenId),
            "You must be the owner to add this NFT!"
        );
        //construct array and add to mapping
        //add to mapping
        ChildNFT memory child;
        child.owner = msg.sender;
        child.childAddress = childTokenAddress;
        child.childTokenId = childTokenId;
        activeMapping[parentTokenId][childTokenCount[parentTokenId]] = true; //add to the end - this should be the child_struct_id
        tokenMapping[parentTokenId].push(child);
        childTokenCount[parentTokenId]++;
        return true;
    }

    function finalizeAndCreateFamilyPhoto(uint256 parentTokenId) public {
        //only the parent nft's owner (creator) can call this.
        require(
            msg.sender == this.ownerOf(parentTokenId),
            "Only the token's creator can finalize this NFT!"
        );
        uint8 tokenState = tokenStatusMap[parentTokenId];   
        require(
            tokenState == uint8(TOKEN_STATUS.IN_PROGRESS),
            "This can't be finalized yet"
        );
        emit finalizeParentNFT(msg.sender);
        tokenStatusMap[parentTokenId] = uint8(TOKEN_STATUS.FINAL);
        checkActiveStatusesAndGenerateImg(parentTokenId);
    }

    function checkActiveStatusesAndGenerateImg(uint256 parent_token_id)
        public
        returns (bool)
    {
        for (
            uint256 child_token_struct_id = 0;
            child_token_struct_id < childTokenCount[parent_token_id];
            child_token_struct_id++
        ) {
            ChildNFT memory childStruct = tokenMapping[parent_token_id][
                child_token_struct_id
            ];
            if (
                activeMapping[parent_token_id][child_token_struct_id] == false
            ) {
                //skip going further if this is child NFT is already inactive
            }
            address childTokenAddress = childStruct.childAddress;
            address childTokenOwner = childStruct.owner;
            uint256 childTokenId = childStruct.childTokenId;
            if (
                proofOfNFT(childTokenAddress, childTokenOwner, childTokenId) ==
                false
            ) {
                killNFT(parent_token_id, child_token_struct_id);
            }
        }
        //call out to EA, which will regen the tokenURI
        bytes32 requestId = requestIPFSURI(parent_token_id);
        requestIdToParentTokenID[requestId] = parent_token_id; //create mapping for EA so the contract can relate the EA Request to the token ID it was for.
        return true;
    }

    function checkActiveStatusesAndRegenerateImgs() internal returns (bool) {
        //used for testing, removing from public function list
        //check ALL tokens. regen ONLY if something changed in the ActiveAddress array
        //for each finalized parent NFT, check that child NFTs (address, token id) are in wallet of owner

        for (
            uint256 parent_token_id = 0;
            parent_token_id < tokenCounter; //less than or equal to if tokencount++ above
            parent_token_id++
        ) {
            //if (tokenStatusMap[parent_token_id] != uint8(TOKEN_STATUS.FINAL)) {
            //    return false;
            //}
            for (
                uint256 child_token_struct_id = 0;
                child_token_struct_id < childTokenCount[parent_token_id];
                child_token_struct_id++
            ) {
                ChildNFT memory childStruct = tokenMapping[parent_token_id][
                    child_token_struct_id
                ];
                if (
                    activeMapping[parent_token_id][child_token_struct_id] ==
                    false
                ) {
                    //skip going further if this is child NFT is already inactive
                }
                address childTokenAddress = childStruct.childAddress;
                address childTokenOwner = childStruct.owner;
                uint256 childTokenId = childStruct.childTokenId;
                if (
                    proofOfNFT(
                        childTokenAddress,
                        childTokenOwner,
                        childTokenId
                    ) == false
                ) {
                    killNFT(parent_token_id, child_token_struct_id);
                }
            }
            //presumably call to EA to gen image. global or do it in the for loop?
            //call out to EA, which will regen the tokenURI
            bytes32 requestId = requestIPFSURI(parent_token_id);
            requestIdToParentTokenID[requestId] = parent_token_id;
        }
        return true;
    }

    function proofOfNFT(
        address tokenAddress,
        address tokenOwner,
        uint256 tokenId
    ) public view returns (bool) {
        ERC721 target_nft = ERC721(tokenAddress);
        if (target_nft.ownerOf(tokenId) != tokenOwner) {
            //set this child token as inactive if owner isn't the stored owner - Proof of NFT
            return false;
        }
        return true;
    }

    /**
     * Create a Chainlink request to do ipfs img manipulation, then return
     */
    function requestIPFSURI(uint256 parent_token_id)
        internal
        returns (bytes32 requestId)
    {
        Chainlink.Request memory request = buildChainlinkRequest(
            jobId,
            address(this),
            this.fulfillBytes.selector
        );
        string[] memory childURIAry = new string[](
            childTokenCount[parent_token_id]
        ); //declare initial size since this string array is in memory. 
        string[] memory activeStrings = new string[](
            childTokenCount[parent_token_id]
        );
        for (
            uint256 child_token_struct_id = 0;
            child_token_struct_id < childTokenCount[parent_token_id];
            child_token_struct_id++
        ) {
            // get a bunch of info about the NFTs added to a parent
            address tokenAddress = tokenMapping[parent_token_id][
                child_token_struct_id
            ].childAddress;
            ERC721 child_nft = ERC721(tokenAddress);
            string memory child_token_uri = child_nft.tokenURI(
                tokenMapping[parent_token_id][child_token_struct_id]
                    .childTokenId
            );
            string memory activeString = "false";
            if (activeMapping[parent_token_id][child_token_struct_id] == true) {
                activeString = "true";
            }
            activeStrings[child_token_struct_id] = activeString; //data still remains at location child_token_struct_id
            childURIAry[child_token_struct_id] = child_token_uri;
        }

        request.addStringArray("activeAry", activeStrings);
        request.addStringArray("URIAry", childURIAry);
        // Sends the request
        requestId = requestOracleData(request, fee);
        return requestId;
    }

    /**
     * Receive the response in the form of bytes to convert to string (defined in job spec)
     */
    function fulfillBytes(bytes32 requestId, bytes memory bytesData)
        public
        recordChainlinkFulfillment(requestId)
    {
        emit RequestFulfilled(requestId, bytesData);
        latestTokenURI = string(bytesData);
        uint256 parent_token_id = requestIdToParentTokenID[requestId];
        setTokenURI(parent_token_id, latestTokenURI);
    }

    function killNFT(uint256 parent_token_id, uint256 child_token_struct_id)
        internal
    {
        activeMapping[parent_token_id][child_token_struct_id] = false;
    }

    function setTokenURI(uint256 tokenId, string memory _tokenURI) public {
        // generate new URI offchain, set it. 
        // require msg.sender is my CL node
        require ((msg.sender=="0x0EBc28BE8687373DF8Fb4AB353f351Ab19694681"),"Only the Family Photo EA job can call this");
        _setTokenURI(tokenId, _tokenURI);
    }

    function checkUpkeep(bytes calldata _checkData) external view returns (bool upkeepNeeded, bytes memory performData) {
        //for use with keepers
        //shoutout linkpool for this https://etherscan.io/address/0xbf3Dc19893A737A15b5f86B1e8d17C532DB4D619#code
        uint256[][] memory tokensToWork = new uint256[][](tokenCounter);
        //run through finalized tokens
        //check to see token owners
        //for those tokens that may have a different owner, flag which in ActiveAry to set to inactive and flag that token to regenerate - then set upkeepNeeded to True
        //set checkData to that info
        for (
            uint256 parent_token_id = 0;
            parent_token_id < tokenCounter;
            parent_token_id++
        ) {
            if (tokenStatusMap[parent_token_id] == uint8(TOKEN_STATUS.FINAL)) {
                //only run on finalized tokens
                tokensToWork[parent_token_id] = new uint256[](childTokenCount[parent_token_id]);
                for (
                    uint256 child_token_struct_id = 0;
                    child_token_struct_id < childTokenCount[parent_token_id];
                    child_token_struct_id++
                ) {
                    ChildNFT memory childStruct = tokenMapping[parent_token_id][
                        child_token_struct_id
                    ];
                    if (
                        activeMapping[parent_token_id][child_token_struct_id] ==
                        true
                    ) {
                        ERC721 target_nft = ERC721(childStruct.childAddress);
                        if (target_nft.ownerOf(childStruct.childTokenId) != childStruct.owner) {
                            tokensToWork[parent_token_id][
                                child_token_struct_id
                            ] = 1;
                            upkeepNeeded = true;
                        } //could put the else statement here but want to be sure other ones get 0s too.
                    }
                    else {
                            tokensToWork[parent_token_id][
                                child_token_struct_id
                            ] = 0;
                        }
                }
            }
        }
        performData = abi.encode(tokensToWork);
    }

    function performUpkeep(bytes calldata performData) external  {
        //given a list of parent token IDs,childtokens in performData, mark childtoken@parentToken as inactive.
        //then regenerate parentTokens
        //TODO - probably add some checks about token balances here. could make the job also top off with link
        bytes memory _data=performData;
        uint256[][] memory tokensToWork = abi.decode(_data, (uint256[][]));
        bool regenflag;
        for (
            uint256 parent_token_id = 0;
            parent_token_id < tokenCounter;
            parent_token_id++
        ) {
            regenflag=false;
            if (tokenStatusMap[parent_token_id] == uint8(TOKEN_STATUS.FINAL)) {
                for (
                    uint256 child_token_struct_id = 0;
                    child_token_struct_id < childTokenCount[parent_token_id];
                    child_token_struct_id++
                ) {
                    if (tokensToWork[parent_token_id][child_token_struct_id] == 1) {
                        killNFT(parent_token_id, child_token_struct_id);
                        regenflag=true;
                    }
                }
                if(regenflag){
                    bytes32 requestId = requestIPFSURI(parent_token_id);
                    requestIdToParentTokenID[requestId] = parent_token_id;
                }
            }
        }
    }
    /*
    //Copying the keeper functions to call manually was a good way to test my keeper job
    function seeUpkeep(bytes calldata checkData)
        public
        returns (bool upkeepNeeded, bytes memory performData)
    {
        //for use with keepers
        //shoutout linkpool for this https://etherscan.io/address/0xbf3Dc19893A737A15b5f86B1e8d17C532DB4D619#code
        uint256[][] memory tokensToWork = new uint256[][](tokenCounter);
        //run through finalized tokens
        //check to see token owners
        //for those tokens that may have a different owner, flag which in ActiveAry to set to inactive and flag that token to regenerate - then set upkeepNeeded to True
        //set checkData to that info
        for (
            uint256 parent_token_id = 0;
            parent_token_id < tokenCounter;
            parent_token_id++
        ) {
            if (tokenStatusMap[parent_token_id] == uint8(TOKEN_STATUS.FINAL)) {
                //only run on finalized tokens
                tokensToWork[parent_token_id] = new uint256[](childTokenCount[parent_token_id]);
                for (
                    uint256 child_token_struct_id = 0;
                    child_token_struct_id < childTokenCount[parent_token_id];
                    child_token_struct_id++
                ) {
                    ChildNFT memory childStruct = tokenMapping[parent_token_id][
                        child_token_struct_id
                    ];
                    if (
                        activeMapping[parent_token_id][child_token_struct_id] ==
                        true
                    ) {
                        //TODO - might need to check this is right...
                        ERC721 target_nft = ERC721(childStruct.childAddress);
                        if (target_nft.ownerOf(childStruct.childTokenId) != childStruct.owner) {
                            tokensToWork[parent_token_id][
                                child_token_struct_id
                            ] = 1;
                            upkeepNeeded = true;
                        } else {
                            tokensToWork[parent_token_id][
                                child_token_struct_id
                            ] = 0;
                        }
                    }
                }
            }
        }
        upkeepvar=upkeepNeeded;
        tokensToWorkvar=tokensToWork;
        performData = abi.encode(tokensToWork);
        if (upkeepNeeded==true){
            testDoUpkeep(performData);
        }
    }
    function testDoUpkeep(bytes memory performData) public {
        //given a list of parent token IDs,childtokens in performData, mark childtoken@parentToken as inactive.
        //then regenerate parentTokens
        //TODO - probably add some checks about token balances here. could make the job also top off with link?
        bytes memory _data=performData;
        uint256[][] memory tokensToWork = abi.decode(_data, (uint256[][]));
        bool regenflag;
        //address[] memory wallets = abi.decode(performData, (address[]));
        for (
            uint256 parent_token_id = 0;
            parent_token_id < tokenCounter;
            parent_token_id++
        ) {
            regenflag=false;
            if (tokenStatusMap[parent_token_id] == uint8(TOKEN_STATUS.FINAL)) {
                for (
                    uint256 child_token_struct_id = 0;
                    child_token_struct_id < childTokenCount[parent_token_id];
                    child_token_struct_id++
                ) {
                    if (tokensToWork[parent_token_id][child_token_struct_id] == 1) {
                        killNFT(parent_token_id, child_token_struct_id);
                        regenflag=true;
                    }
                }
                if(regenflag){
                    bytes32 requestId = requestIPFSURI(parent_token_id);
                    requestIdToParentTokenID[requestId] = parent_token_id;
                }
            }
        }
    }*/
}
