from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
addr = "0x4f50E3feDBb7b691b10034Ad097914B428853891"
eth = w3.eth.get_balance(addr)
print(f"ETH: {w3.from_wei(eth, 'ether')}")
token = w3.eth.contract(
    address=Web3.to_checksum_address("0x240b09731D96979f50B2C649C9CE10FcF9C7987F"),
    abi=[
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf",
         "outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[],"name":"decimals",
         "outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    ]
)
raw = token.functions.balanceOf(addr).call()
dec = token.functions.decimals().call()
print(f"OPG: {raw / 10**dec:.4f}")
