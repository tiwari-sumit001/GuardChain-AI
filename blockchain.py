from web3 import Web3
import json
import os
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
ganache_url = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")
web3 = Web3(Web3.HTTPProvider(ganache_url, request_kwargs={"timeout": 2}))

contract = None
contract_address = None
abi = None
ganache_connected = False

# Local Python list to act as a fallback blockchain simulation
simulated_logs = []

def check_and_deploy_contract():
    global contract, contract_address, abi, ganache_connected
    
    if not web3.is_connected():
        print("[WARNING] Ganache not connected on http://127.0.0.1:7545. Falling back to local simulation.")
        ganache_connected = False
        return False
        
    ganache_connected = True
    accounts = web3.eth.accounts
    if not accounts:
        print("[WARNING] No Ganache accounts found. Falling back to local simulation.")
        return False
        
    deployer = accounts[0]
    details_path = ROOT / "static" / "contract_details.json"
    
    if not os.path.exists(details_path):
        print("[ERROR] contract_details.json not found. Run compile_sol.py first!")
        return False
        
    with open(details_path, "r") as f:
        details = json.load(f)
        
    abi = details["abi"]
    bytecode = details["bytecode"]
    contract_address = details.get("address", "")
    
    # Check if contract is already deployed and exists on-chain
    is_valid_deployment = False
    if contract_address:
        try:
            code = web3.eth.get_code(contract_address)
            # If code is not '0x' or empty, the contract exists on-chain
            if code and code != web3.to_bytes(hexstr="0x"):
                is_valid_deployment = True
                print(f"[INFO] Connected to existing smart contract at: {contract_address}")
        except Exception as e:
            print("[WARNING] Verification of contract address failed, will redeploy:", e)
            
    if not is_valid_deployment:
        print("[INFO] Deploying new smart contract to Ganache...")
        try:
            # Instantiate contract factory
            ContractFactory = web3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Submit deployment transaction
            tx_hash = ContractFactory.constructor().transact({
                'from': deployer,
                'gas': 3000000
            })
            
            # Wait for receipt
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
            contract_address = tx_receipt.contractAddress
            
            # Save address back to details
            details["address"] = contract_address
            with open(details_path, "w") as f:
                json.dump(details, f, indent=4)
                
            print(f"[SUCCESS] Smart contract deployed at address: {contract_address}")
        except Exception as e:
            print("[ERROR] Failed to deploy smart contract:", e)
            return False
            
    # Load the contract object
    contract = web3.eth.contract(address=contract_address, abi=abi)
    return True

# Initialize blockchain details on import if possible
try:
    check_and_deploy_contract()
except Exception as e:
    print("[WARNING] Initial blockchain initialization failed. Will retry on demand:", e)

def store_on_blockchain(amount, result, sender="Anonymous", receiver="Fraud Portal"):
    """
    Log a fraudulent transaction. Uses Ganache if connected, otherwise falls back to local simulation.
    """
    global contract, ganache_connected, simulated_logs
    
    # Retry connection if not connected
    if not ganache_connected or contract is None:
        check_and_deploy_contract()
            
    if not ganache_connected or contract is None:
        # SIMULATION FALLBACK
        print("[SIMULATION] Blockchain offline. Logging fraud to simulation state.")
        sim_record = {
            "index": len(simulated_logs),
            "amount": int(float(amount)),
            "result": result,
            "sender": sender,
            "receiver": receiver,
            "timestamp": int(time.time()),
            "status": 0, # Flagged
            "ledger_mode": "simulation"
        }
        simulated_logs.append(sim_record)
        return {
            "mode": "simulation",
            "simulation_id": str(uuid4()),
            "tx_hash": None,
            "block_number": None,
            "gas_used": None,
            "contract_address": None
        }
            
    try:
        # Ganache account to send transaction
        account = web3.eth.accounts[0]
        amt_int = int(float(amount))
        
        tx_hash = contract.functions.storeTransaction(
            amt_int,
            result,
            sender,
            receiver
        ).transact({
            'from': account,
            'gas': 3000000
        })
        
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
        print(f"[SUCCESS] Transaction recorded on blockchain. Tx Hash: {receipt.transactionHash.hex()}")
        return {
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "contract_address": contract_address,
            "mode": "ganache"
        }
    except Exception as e:
        print("[ERROR] Failed to write transaction to blockchain, saving to simulation fallback:", e)
        # Simulation fallback
        sim_record = {
            "index": len(simulated_logs),
            "amount": int(float(amount)),
            "result": result,
            "sender": sender,
            "receiver": receiver,
            "timestamp": int(time.time()),
            "status": 0, # Flagged
            "ledger_mode": "simulation"
        }
        simulated_logs.append(sim_record)
        return {
            "mode": "simulation",
            "simulation_id": str(uuid4()),
            "tx_hash": None,
            "block_number": None,
            "gas_used": None,
            "contract_address": None
        }

def update_on_blockchain(index, status_code):
    """
    Update the status of a logged fraud record. Restricted to authorized nodes on Ganache.
    """
    global contract, ganache_connected, simulated_logs
    index = int(index)
    status_code = int(status_code)
    if index < 0 or status_code not in (0, 1, 2, 3):
        raise ValueError("index must be non-negative and status must be between 0 and 3")
    
    # Retry connection if not connected
    if not ganache_connected or contract is None:
        check_and_deploy_contract()
            
    if not ganache_connected or contract is None:
        # SIMULATION FALLBACK
        print(f"[SIMULATION] Blockchain offline. Updating status of record #{index} to {status_code}.")
        if index < len(simulated_logs):
            simulated_logs[index]["status"] = int(status_code)
            return {
                "mode": "simulation",
                "simulation_id": str(uuid4()),
                "tx_hash": None,
                "block_number": None,
                "gas_used": None
            }
        return None
            
    try:
        account = web3.eth.accounts[0]
        tx_hash = contract.functions.updateTransactionStatus(
            int(index),
            int(status_code)
        ).transact({
            'from': account,
            'gas': 3000000
        })
        
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
        print(f"[SUCCESS] Record status updated on blockchain. Tx Hash: {receipt.transactionHash.hex()}")
        return {
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "mode": "ganache"
        }
    except Exception as e:
        print("[ERROR] Failed to update transaction status on blockchain, updating in simulation:", e)
        if index < len(simulated_logs):
            simulated_logs[index]["status"] = int(status_code)
            return {
                "mode": "simulation",
                "simulation_id": str(uuid4()),
                "tx_hash": None,
                "block_number": None,
                "gas_used": None
            }
        return None

def get_blockchain_logs():
    """
    Fetch all fraud records. Combines/returns live Ganache logs or simulated local logs.
    """
    global contract, ganache_connected, simulated_logs
    
    if not ganache_connected or contract is None:
        check_and_deploy_contract()
            
    if not ganache_connected or contract is None:
        return list(reversed(simulated_logs))
            
    try:
        count = contract.functions.getTransactionCount().call()
        logs = []
        for i in range(count):
            record = contract.functions.getTransaction(i).call()
            # Solidity returns (amount, result, senderName, receiverName, timestamp, status)
            logs.append({
                "index": i,
                "amount": record[0],
                "result": record[1],
                "sender": record[2],
                "receiver": record[3],
                "timestamp": record[4],
                "status": record[5],
                "ledger_mode": "ganache"
            })
        return list(reversed(logs))
    except Exception as e:
        print("[ERROR] Failed to fetch transaction logs from blockchain, returning simulation logs:", e)
        return list(reversed(simulated_logs))

def get_network_status():
    """
    Retrieve Ganache network connection information.
    """
    global contract_address, ganache_connected
    
    connected = web3.is_connected()
    ganache_connected = connected
    
    if not connected:
        return {
            "status": "Offline (Simulation Mode Active)",
            "provider": ganache_url,
            "block_number": 0,
            "active_account": "None (Local Admin)",
            "contract_address": None,
            "mode": "simulation"
        }
        
    try:
        block_num = web3.eth.block_number
        accounts = web3.eth.accounts
        active_acc = accounts[0] if accounts else "None"
        addr = contract_address if contract_address else "Not Deployed"
        
        return {
            "status": "Connected",
            "provider": ganache_url,
            "block_number": block_num,
            "active_account": active_acc,
            "contract_address": addr,
            "mode": "ganache"
        }
    except Exception as e:
        return {
            "status": "Error",
            "provider": ganache_url,
            "block_number": 0,
            "active_account": "None",
            "contract_address": str(e),
            "mode": "error"
        }
