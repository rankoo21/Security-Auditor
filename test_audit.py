"""Quick test: send a tiny contract to the audit API."""
import requests, json

code = """
pragma solidity ^0.8.0;
contract Test {
    address public owner;
    constructor() { owner = msg.sender; }
    function withdraw() public {
        payable(msg.sender).transfer(address(this).balance);
    }
}
"""

print("Sending audit request...")
try:
    r = requests.post("http://localhost:5000/api/audit",
                       json={"code": code}, timeout=120)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
except Exception as e:
    print(f"Error: {e}")
