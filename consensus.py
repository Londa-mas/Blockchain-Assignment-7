"""
BLCH9X2 — Assignment 7: Consensus and Forks (consensus.py)
Module for simulating nodes, resolving forks, and computing confirmations.
"""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable

Block = dict[str, Any]
Chain = list[Block]

DIFFICULTY = 2  # Classroom toy difficulty


def _sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _header_hash(index, timestamp, txs, previous_hash, nonce) -> str:
    payload = json.dumps(
        {
            "index": index,
            "timestamp": timestamp,
            "transactions": txs,
            "previous_hash": previous_hash,
            "nonce": nonce,
        },
        sort_keys=True,
    )
    return _sha(payload)


def mine_block(
    index: int, txs: list[dict[str, Any]], previous_hash: str, difficulty: int = DIFFICULTY
) -> Block:
    """Proof-of-work search until the hash has `difficulty` leading hex zeros."""
    timestamp = time.time()
    nonce = 0
    while True:
        h = _header_hash(index, timestamp, txs, previous_hash, nonce)
        if h.startswith("0" * difficulty):
            return {
                "index": index,
                "timestamp": timestamp,
                "transactions": txs,
                "previous_hash": previous_hash,
                "nonce": nonce,
                "hash": h,
                "difficulty": difficulty,
            }
        nonce += 1


def verify_chain(chain: Chain, difficulty: int = DIFFICULTY) -> bool:
    """Return True iff hashes, parent links, and PoW difficulty checks pass."""
    if not chain:
        return False
    for i, block in enumerate(chain):
        expected = _header_hash(
            block["index"],
            block["timestamp"],
            block["transactions"],
            block["previous_hash"],
            block["nonce"],
        )
        if block.get("hash") != expected:
            return False
        diff = int(block.get("difficulty", difficulty))
        if not str(block["hash"]).startswith("0" * diff):
            return False
        if i == 0:
            continue
        if block["previous_hash"] != chain[i - 1]["hash"]:
            return False
        if block["index"] != i:
            return False
    return True


def chain_work(chain: Chain) -> int:
    """Heaviest-work score: cumulative sum of per-block difficulties."""
    total = 0
    for block in chain:
        total += int(block.get("difficulty", DIFFICULTY))
    return total


@dataclass
class Node:
    """A simulated peer holding its own view of the chain."""

    name: str
    chain: Chain = field(default_factory=list)

    def tip(self) -> Block:
        if not self.chain:
            raise ValueError(f"node {self.name} has an empty chain")
        return self.chain[-1]

    def height(self) -> int:
        return len(self.chain) - 1 if self.chain else -1

    def summary(self) -> str:
        tip_short = self.tip()["hash"][:10]
        return (
            f"{self.name}: height={self.height()} tip={tip_short}... "
            f"valid={verify_chain(self.chain)} work={chain_work(self.chain)}"
        )


def tie_break(chains: list[Chain]) -> Chain:
    """Lexicographically smaller tip hash tie-break policy."""
    return min(chains, key=lambda c: c[-1]["hash"])


def resolve_fork(
    chains: list[Chain], verifier: Callable[[Chain], bool] | None = None
) -> Chain:
    """Among valid chains, return a deep copy of the winning chain based on heaviest work."""
    verify = verifier or verify_chain
    valid = [c for c in chains if verify(c)]
    if not valid:
        raise ValueError("no valid chain found")
    best = max(chain_work(c) for c in valid)
    tied = [c for c in valid if chain_work(c) == best]
    chosen = tied[0] if len(tied) == 1 else tie_break(tied)
    return deepcopy(chosen)


def sync_nodes(nodes: list[Node]) -> Chain:
    """Resolve all node chains and set every node to the winning chain (deep copy)."""
    winner = resolve_fork([n.chain for n in nodes])
    for node in nodes:
        node.chain = deepcopy(winner)
    return winner


def find_tx_height(chain: Chain, tx_id: str) -> int | None:
    """Return the block index containing tx_id, or None if absent."""
    for block in chain:
        for tx in block.get("transactions", []):
            if tx.get("id") == tx_id:
                return int(block["index"])
    return None


def confirmations(chain: Chain, tx_id: str) -> int:
    """Compute confirmation depth k = H - h + 1 for a transaction ID."""
    h = find_tx_height(chain, tx_id)
    if h is None or not chain:
        return 0
    tip_h = int(chain[-1]["index"])
    return tip_h - h + 1


def demo_fork_scenario() -> dict[str, Any]:
    """Execute end-to-end fork creation, extension, and resolution."""
    genesis = mine_block(0, [{"note": "genesis"}], "0" * 64)
    a = Node("A", [deepcopy(genesis)])
    b = Node("B", [deepcopy(genesis)])
    c = Node("C", [deepcopy(genesis)])

    a.chain.append(
        mine_block(1, [{"id": "pay-alice", "amount": 10000}], a.tip()["hash"])
    )
    b.chain.append(
        mine_block(1, [{"id": "pay-bob", "amount": 10000}], b.tip()["hash"])
    )
    a.chain.append(mine_block(2, [{"note": "extend-A"}], a.tip()["hash"]))

    before = {"A": a.height(), "B": b.height(), "C": c.height()}
    sync_nodes([a, b, c])
    return {
        "heights_before": before,
        "tip_after": a.tip()["hash"],
        "canonical_tx": a.chain[1]["transactions"][0]["id"],
        "confirmations_alice": confirmations(a.chain, "pay-alice"),
        "confirmations_bob": confirmations(a.chain, "pay-bob"),
    }


if __name__ == "__main__":
    print(json.dumps(demo_fork_scenario(), indent=2))