import json
import os
import solcx

print("Installing Solidity compiler 0.8.19...")
try:
    solcx.install_solc("0.8.19")
    print("Solidity compiler 0.8.19 installed successfully.")
except Exception as e:
    print("Solidity compiler installation failed:", e)

print("Compiling contracts/FraudRegistry.sol...")
try:
    compiled_sol = solcx.compile_files(["contracts/FraudRegistry.sol"], output_values=["abi", "bin"], solc_version="0.8.19")
    # Note: solc output keys depend on version and paths. Let's find the correct key.
    contract_key = None
    for key in compiled_sol.keys():
        if "FraudRegistry" in key:
            contract_key = key
            break
            
    if contract_key:
        contract_interface = compiled_sol[contract_key]
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        
        os.makedirs("static", exist_ok=True)
        # We save it. If there was a previously deployed address, we might want to preserve it.
        address = ""
        details_path = "static/contract_details.json"
        if os.path.exists(details_path):
            try:
                with open(details_path, "r") as f:
                    old_details = json.load(f)
                address = old_details.get("address", "")
            except:
                pass
                
        with open(details_path, "w") as f:
            json.dump({
                "abi": abi,
                "bytecode": bytecode,
                "address": address
            }, f, indent=4)
        print("[SUCCESS] Contract compiled successfully! Details saved to static/contract_details.json")
    else:
        print("[ERROR] FraudRegistry contract not found in compiled outputs. Keys:", compiled_sol.keys())
except Exception as e:
    print("[ERROR] Solidity compilation failed:", e)
