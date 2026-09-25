# BLCH9X2 — Assignment 7: Consensus and Forks (Part A)

**Course:** Master of Financial Engineering (MFE), University of Johannesburg  
**Module:** BLCH9X2 Blockchain  
**Group Members:** O.T.H Masuku, P.T. Molete, & M.M. Moketla

---

## Overview
This repository contains the core consensus engine and node simulation framework for Assignment 7. The module models peer-to-peer state divergence, Proof-of-Work (PoW) fork creation, heaviest-work resolution, reorganisation handling, and remittance confirmation depth calculation ($k$).

## Project Structure
- `consensus.py`: Core simulation module featuring the `Node` API, chain validation (`verify_chain`), cumulative work scoring (`chain_work`), deterministic tie-breaks, and confirmation metrics.
- `tests.py`: Automated test suite verifying cryptographic integrity and consensus correctness.

## Installation & Running
1. Clone the repository:
   ```bash
   git clone [https://github.com/Londa-mas/Blockchain-Assignment-7.git](https://github.com/Londa-mas/Blockchain-Assignment-7.git)
   cd Blockchain-Assignment-7
   ```
2. Verify Python 3.10+ (pure standard library implementation; no external dependencies required).
3. Run the end-to-end fork scenario simulation:
   ```bash
   python consensus.py
   ```
4. Run the automated test suite:
   ```bash
   python tests.py
   ```
