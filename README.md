# zkVerify PoC: Economic Denial of Service (DoS) via Atomic Batch Poisoning

## 1. Vulnerability Overview
This Proof of Concept (PoC) demonstrates a **Gas-Draining Denial of Service (DoS)** attack targeting relayers that utilize the Substrate `Utility.batch_all` (atomic batching) functionality to submit ZK proofs to the **zkVerify** network.

The core of the vulnerability lies in the **Cost Asymmetry** between proof generation/injection and proof verification. An attacker can inject malformed or "poisoned" proofs into a relayer's processing queue at near-zero cost. When the relayer attempts to process these proofs in an atomic batch (`batch_all`), the entire transaction is reverted upon encountering a single invalid proof. However, the relayer is still charged the full gas fee for the entire batch.

## 2. Impact
- **Relayer Bankruptcy:** Attackers can continuously drain a relayer's funds (VFY) by forcing failed batch transactions.
- **Service Disruption:** Legitimate user proofs included in the poisoned batch are not processed, causing significant delays and breaking the reliability of the modular verification service.
- **Mempool Congestion:** The network is flooded with failed extrinsics that still consume block space and validator resources.

## 3. PoC Components
- `src/database.py`: Manages the local proof hopper (SQLite).
- `src/exploit.py`: Simulates an attacker injecting a single "poisoned" proof into the hopper.
- `src/relayer.py`: A vulnerable relayer implementation using `Utility.batch_all`.
- `run_demo.py`: An orchestration script to demonstrate the balance drainage.

## 4. Prerequisites
- Python 3.10+
- A running zkVerify node (Local or Testnet).
- A relayer account with some VFY for gas.

## 5. Reproduction Steps
1. Configure your `.env` with `RELAYER_MNEMONIC` and `ZKVERIFY_RPC_URL`.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the demo: `python run_demo.py`

Observe how the relayer's balance decreases while 0 proofs are verified due to the atomic batch failure.

---
*Authored by: roru (zkVerify Security Researcher)*
