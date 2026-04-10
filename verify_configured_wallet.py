import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
pk = os.environ.get("OG_PRIVATE_KEY")
w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
acct = w3.eth.account.from_key(pk)
addr = acct.address
print(f"Address: {addr}")

OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
contract = w3.eth.contract(address=OPG, abi=ABI)
balance = contract.functions.balanceOf(addr).call()
print(f"OPG Balance: {round(balance/1e18, 4)}")
