"""
BLCH9X2 — Assignment 7 Test Suite (tests.py)
Automated tests verifying consensus rules, chain validation, fork resolution, 
and confirmation depth metrics.
"""

from __future__ import annotations

import unittest
from copy import deepcopy

from consensus import (
    DIFFICULTY,
    Node,
    chain_work,
    confirmations,
    demo_fork_scenario,
    find_tx_height,
    mine_block,
    resolve_fork,
    sync_nodes,
    verify_chain,
)


class TestConsensusEngine(unittest.TestCase):
    """Test suite for UJ MFE BLCH9X2 Assignment 7 Consensus & Forks module."""

    def setUp(self) -> None:
        """Set up standard genesis block and basic nodes for testing."""
        self.genesis = mine_block(0, [{"note": "genesis"}], "0" * 64)

    def test_genesis_verification(self) -> None:
        """Ensure a single genesis block verifies successfully and has correct work."""
        self.assertTrue(verify_chain([self.genesis]))
        self.assertEqual(chain_work([self.genesis]), DIFFICULTY)

    def test_invalid_chain_rejection(self) -> None:
        """Ensure altered header hashes or broken links fail verification immediately."""
        bad_chain = [deepcopy(self.genesis)]
        # Tamper with the hash without recomputing
        bad_block = dict(bad_chain[0])
        bad_block["hash"] = "00" + "f" * 62
        bad_chain[0] = bad_block

        self.assertFalse(verify_chain(bad_chain))

    def test_chain_work_scoring(self) -> None:
        """Verify cumulative work sums correctly over multiple blocks."""
        b1 = mine_block(1, [{"id": "tx1"}], self.genesis["hash"])
        b2 = mine_block(2, [{"id": "tx2"}], b1["hash"])
        chain = [self.genesis, b1, b2]
        
        expected_work = DIFFICULTY * 3
        self.assertEqual(chain_work(chain), expected_work)

    def test_fork_resolution_heaviest_work(self) -> None:
        """Ensure the branch with heavier work wins resolution, rejecting invalid long chains."""
        # Short branch with 2 blocks (Work = 4)
        branch_short = [
            deepcopy(self.genesis),
            mine_block(1, [{"id": "pay-a"}], self.genesis["hash"]),
            mine_block(2, [{"id": "pay-b"}], self.genesis["hash"]) # Wait, need proper parent linking for valid chain
        ]
        # Let's construct valid competing branches properly:
        b1_a = mine_block(1, [{"id": "pay-alice"}], self.genesis["hash"])
        b2_a = mine_block(2, [{"note": "ext-a"}], b1_a["hash"])
        chain_a = [deepcopy(self.genesis), b1_a, b2_a]  # Length 3, Work 6

        b1_b = mine_block(1, [{"id": "pay-bob"}], self.genesis["hash"])
        chain_b = [deepcopy(self.genesis), b1_b]          # Length 2, Work 4

        # Winner should be chain_a due to higher cumulative work
        winner = resolve_fork([chain_b, chain_a])
        self.assertEqual(len(winner), 3)
        self.assertEqual(winner[1]["transactions"][0]["id"], "pay-alice")

    def test_deterministic_tie_break(self) -> None:
        """Ensure equal work chains resolve deterministically via lexicographical tip hash."""
        b1_1 = mine_block(1, [{"id": "tx-one"}], self.genesis["hash"])
        b1_2 = mine_block(1, [{"id": "tx-two"}], self.genesis["hash"])

        chain_1 = [deepcopy(self.genesis), b1_1]
        chain_2 = [deepcopy(self.genesis), b1_2]

        # Test order independence
        winner_1 = resolve_fork([chain_1, chain_2])
        winner_2 = resolve_fork([chain_2, chain_1])

        self.assertEqual(winner_1[-1]["hash"], winner_2[-1]["hash"])

    def test_node_synchronisation(self) -> None:
        """Verify sync_nodes updates all peer nodes to the winning canonical chain."""
        node_a = Node("A", [deepcopy(self.genesis)])
        node_b = Node("B", [deepcopy(self.genesis)])

        b1 = mine_block(1, [{"id": "tx-sync"}], self.genesis["hash"])
        b2 = mine_block(2, [{"note": "ext"}], b1["hash"])
        
        node_a.chain = [deepcopy(self.genesis), b1, b2]
        node_b.chain = [deepcopy(self.genesis), b1]

        sync_nodes([node_a, node_b])

        self.assertEqual(node_a.chain[-1]["hash"], node_b.chain[-1]["hash"])
        self.assertEqual(len(node_a.chain), 3)

    def test_confirmation_depth_calculation(self) -> None:
        """Verify formula k = H - h + 1 computes correctly."""
        b1 = mine_block(1, [{"id": "remittance-10k", "amount": 10000}], self.genesis["hash"])
        b2 = mine_block(2, [{"note": "pad-1"}], b1["hash"])
        b3 = mine_block(3, [{"note": "pad-2"}], b2["hash"])
        
        chain = [deepcopy(self.genesis), b1, b2, b3]

        # Transaction is at height h=1, tip height H=3 -> k = 3 - 1 + 1 = 3
        self.assertEqual(find_tx_height(chain, "remittance-10k"), 1)
        self.assertEqual(confirmations(chain, "remittance-10k"), 3)
        self.assertEqual(confirmations(chain, "non-existent"), 0)

    def test_demo_fork_scenario_output(self) -> None:
        """Verify the integrated demo scenario fulfills all state expectations."""
        summary = demo_fork_scenario()
        self.assertEqual(summary["canonical_tx"], "pay-alice")
        self.assertEqual(summary["confirmations_bob"], 0)
        self.assertGreaterEqual(summary["confirmations_alice"], 1)


if __name__ == "__main__":
    unittest.main()