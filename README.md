# Family-Photo
For the Chainlink Fall Hackathon 2021.
# Background
This project allows a user to create a Family Photo NFT (FAM). A Family Photo is an ERC-721 where each token stores pointers to other ERC-721 NFTs. 
A user will mint a new FAM which opens it up for that user or other users to "add" their own NFTs to it. "Add" being used loosely here - there isn't any actual token transfer.
At some point, the minting user can decide to "finalize" the FAM they minted, which will generate an image for that FAM based on all the NFTs added to it. This is done via a custom Chainlink External Adapter currently deployed to Kovan (until my Linkpool node expires) Right now mainly IPFS image URI, URLs, or JSON are supported ways to find that image.
Then, if a person who added their NFT to a FAM ever moves that NFT from their wallet, the FAM will automatically regenerate a new image with that NFT blacked out (well - darkened out). This is triggered via a Keeper job currently running on Kovan.

# What
This project contains Solidity and Python deployment scripts for Family Photo. Currently deployed to Kovan at 0xf7FEB6D989b74c47E0DeB54aC6eFD1aB3412e8cb

# Setup
1. This is just the Solidity file for the ParentNFT (Family Photo) contract and a quick ChildNFT test contract as well.
2. See https://github.com/bnstrhbn/IPFS-NFT-EA/tree/master to pull down the Chainlink External Adapter code I'm using and deploy it on a node.
3. See https://github.com/bnstrhbn/Family-Photo-Frontend to pull down a basic React frontend to interact with these contracts if you don't want to use Etherscan. 

## Requirements
Overall - 
1. I used VSCode, Brownie, and React. Install those. 
1a. My Python code also heavily used Pillow, install that
2. I also used Ganache-CLI for testing locally, install that.
2a. To test the EA locally, you can use Docker, install that if you want.
3. I deployed and did integrated testing on Kovan with a couple different accounts.

External Adapter - 
1. Infura key for Infura IPFS beta, I used Linkpool NaaS for my Kovan node, deployed my Python code as an AWS Lambda function
2. Frontend - Alchemy key used in frontend

## Setting Up And Deploying The Solidity Contracts
1. Open up VSCode and fill out your .env to set up your accounts on Kovan etc.
1a. If deploying your own Chainlink node and External Adapter, change the Oracle address, jobID, and fee variables as appropriate.
2. "brownie compile"
3. "brownie run scripts/deploy.py --network=kovan" to run an overall deployment script to Kovan - this deploys the Family Photo ParentNFT.sol contract and a couple ChildNFT contracts to test with.
3a. Remember to fund the ParentNFT contract with LINK!
4. Now interact via Etherscan or the frontend. You can Create a New FAM, Add NFTs to open FAMs, or Finalize FAMs. Then to see the Keeper/EA interaction, move an added NFT between wallets to see the regenerated image.

## Setting Up And Deploying The External Adapter
### Python
1. I mostly followed these steps for deploying my Python code to Docker for local testing and AWS for the EA: https://github.com/thodges-gh/CL-EA-Python-Template
2. To work with Docker, had to add Pillow as a requirement to the pipfile. 
3. To work on AWS I followed the Lambda function instructions from the link above too. In addition, I added two Layers to my function. Pillow and requests from Klayers (https://github.com/keithrozario/Klayers). I also set the timeout to several minutes in case processing takes a while - it seemed like IPFS took a while to upload an image sometimes.

### Chainlink Node and External Adapter job
1. I used Linkpool's Naas for this - it's on Kovan so can work with Keepers and easy to setup! So do that first.
2. In order to process jobs, you need to deploy your Oracle smart contract and have it point at your node's address. This project uses "large responses" (https://docs.chain.link/docs/large-responses/) so you need to deploy the Operator.sol contract rather than the Oracle.sol - https://github.com/smartcontractkit/chainlink/blob/develop/contracts/src/v0.7/Operator.sol
3. I created a new Bridge and new Job (JSON, not TOML :/) to call out to my Lambda function. See EAJob.txt in the EA git repository.

## Setting up the Keeper Job
1. Navigate to https://keepers.chain.link/kovan
2. Register new Upkeep
3. Set the fields - importantly, the Upkeep Address should be the address of your ParentNFT contract and the Gas limit should be max (2500000). Start it out with plenty of LINK.

## Setting up the Frontend
1. Change contract address variables to point to your ParentNFT contract deployed on Kovan. Add your Alchemy Key to a .env file (used in index.tsx as config with @usedapp)
2. You may need to regenerate the ABI jsons using: npx typechain --target ethers-v5 --out-dir src/abis/types './src/abis/*.json'
3. "yarn start" to run this on localhost.

Example of what the front end looks like!
![Alt text](./frontend_example.png?raw=true "Frontend Example")

## Future enhancements
There's a lot of cool things that could be done to enhance this project - really basically, it would be fun to add support for OpenSea's generic NFT structure and for CryptoPunks. I think that this could be a cool thing for NFT (Profile Pic)-based DAO-like groups like Bored Ape Yacht Club members to mint Family Photos of groups of members to show that they all have "iron hands" and will never get rid of their NFTs. Given that might be a cool use-case for this project, it would be cool to be able for the original minting user to specify a given dimension of the resulting image so they can determine how they want to use it ahead of time - for example, your Twitter banner requires a different image ratio than something like a profile picture. 

I also wanted to get into using Filecoin instead of IPFS but didn't have time to get that running. Ideally if you're storing images to NFTs like this you have something safely persistent other than IPFS. On a related note, in a real deployment you'd probably want NFT-contributing users to send LINK/FIL or payment to convert to LINK and FIL along when they add their NFT to a Family Photoin order to cover future costs of maintaining the NFTs.

In my mind, the top really cool enhancements to this project are:
1) Cross-chain pointers via CCIP - since my NFTs are just storing pointers to NFTs, why not deploy this contract on a less gas-intensive L1 or L2 like Avalanche or Arbitrum and just point to NFTs on Ethereum mainnet? Most of the big NFT projects at this point are on mainnet but gas costs would be too prohibitive to allow this project to really work there.  Now that I'm thinking about it, since my EA is ultimately handling my pointers and image manipulation, it might be reasonable to add some ability to check pointers across multiple chains in there.
2) Think of something like GIMP as the image manipulation tool here rather than simply tiling out the image URIs. Given a really cool image manipulation layer on top of the frontend, you could do really cool collages of NFTs all mashed on top of each other in unique ways that then still black out if a user moves them.
