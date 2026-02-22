import os, json, opengradient as og
from dotenv import load_dotenv
load_dotenv()

client = og.Client(private_key=os.environ.get("OG_PRIVATE_KEY"))

code = """pragma solidity ^0.7.0;
contract VulnerableVault {
    mapping(address => uint256) public balances;
    address public owner;
    constructor() { owner = msg.sender; }
    function deposit() public payable { balances[msg.sender] += msg.value; }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
    }
    function transferOwnership(address newOwner) public { owner = newOwner; }
}"""

# Try mimicking app.py exactly
messages = [
    {"role": "system", "content": "Analyze the Solidity code for security issues. Return JSON ONLY: {\"summary\":\"...\",\"risk_score\":0,\"vulnerabilities\":[]}"},
    {"role": "user", "content": f"Audit this Solidity contract:\n\n```solidity\n{code}\n```"}
]

print("Testing with BATCH settlement...")
try:
    r = client.llm.chat(
        model=og.TEE_LLM.GPT_4_1_2025_04_14,
        messages=messages,
        max_tokens=1000,
        temperature=0.1,
        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
    )
    print("SUCCESS (Batch)!")
except Exception as e:
    print(f"FAIL (Batch): {e}")

print("\nTesting with IMMEDIATE settlement...")
try:
    r = client.llm.chat(
        model=og.TEE_LLM.GPT_4_1_2025_04_14,
        messages=messages,
        max_tokens=1000,
        temperature=0.1,
        x402_settlement_mode=og.x402SettlementMode.SETTLE_IMMEDIATE
    )
    print("SUCCESS (Immediate)!")
except Exception as e:
    print(f"FAIL (Immediate): {e}")
