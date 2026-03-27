"""
relayer.py
A vulnerable relayer implementation that uses `Utility.batch_all`.
It does not inspect the individual events of the batch receipt,
leading to incorrect status marking in the database.
"""
import json
import os
from substrateinterface import SubstrateInterface, Keypair
from dotenv import load_dotenv

class VulnerableRelayer:
    def __init__(self, db_manager):
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        self.db = db_manager
        self.mnemonic = os.getenv("RELAYER_MNEMONIC")
        self.rpc_url = os.getenv("ZKVERIFY_RPC_URL", "ws://127.0.0.1:9944")
        self.substrate = None
        self.keypair = None
        # VK Hash for groth16_arkworks_bn254, assuming it's pre-registered
        self.vk_hash = "0x5535d2c95cb9a7d8ef5f06608aa91ec6bbe19a348e3865cdcc1dfb8b0d57c061"

    def _connect(self):
        """Initializes connection to the substrate node."""
        if not self.substrate:
            print("[Relayer] Connecting to zkVerify node...")
            self.substrate = SubstrateInterface(url=self.rpc_url)
            self.keypair = Keypair.create_from_mnemonic(self.mnemonic)
        print(f"[Relayer] Connected as: {self.keypair.ss58_address}")

    def get_balance(self):
        """Returns the free (spendable) balance of the relayer."""
        self._connect()
        account_info = self.substrate.query("System", "Account", [self.keypair.ss58_address])
        balance = account_info.value['data']['free'] / 10**18
        return balance

    def run_batch(self):
        """Fetches pending proofs and submits them in a single atomic batch."""
        self._connect()
        pending_proofs = self.db.get_pending_proofs(limit=10)
        if not pending_proofs:
            print("[Relayer] No pending proofs to submit.")
            return

        print(f"[Relayer] Found {len(pending_proofs)} pending proofs. Composing batch...")
        calls = []
        processed_ids = []

        for proof_row in pending_proofs:
            p_id, _, _, _, p_a, p_b, p_c, pubs, _, _, _ = proof_row
            proof_payload = {"curve": "Bn254", "proof": {"a": p_a, "b": p_b, "c": p_c}}
            pubs_payload = [p for p in json.loads(pubs)]
            
            call = self.substrate.compose_call(
                call_module="SettlementGroth16Pallet",
                call_function="submit_proof",
                call_params={
                    "vk_or_hash": {"Hash": self.vk_hash},
                    "proof": proof_payload,
                    "pubs": pubs_payload,
                    "domain_id": None
                }
            )
            calls.append(call)
            processed_ids.append(p_id)

        print("[Relayer] Submitting `Utility.batch_all` extrinsic...")
        batch_call = self.substrate.compose_call(
            call_module="Utility",
            call_function="batch_all",
            call_params={"calls": calls}
        )

        try:
            extrinsic = self.substrate.create_signed_extrinsic(call=batch_call, keypair=self.keypair)
            receipt = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            if receipt.is_success:
                print(f"[Relayer] ✅ Extrinsic successful. Hash: {receipt.extrinsic_hash}")
                print("[Relayer] CRITICAL FLAW: Marking all proofs as 'verified' without checking events.")
                for p_id in processed_ids:
                    self.db.mark_status(p_id, "verified", receipt.extrinsic_hash)
            else:
                print(f"[Relayer] ❌ Extrinsic failed. Error: {receipt.error_message}")
                for p_id in processed_ids:
                    self.db.mark_status(p_id, "failed", str(receipt.error_message))
        
        except Exception as e:
            print(f"[Relayer] ❌ Critical exception during submission: {e}")
            for p_id in processed_ids:
                self.db.mark_status(p_id, "failed", str(e))
        finally:
            if self.substrate:
                self.substrate.close()
                print("[Relayer] Connection closed.")
