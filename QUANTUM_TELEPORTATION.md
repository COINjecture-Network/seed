# Quantum Teleportation Demo

This script demonstrates quantum teleportation using Qiskit, implementing the famous quantum teleportation protocol to transfer a quantum state from one qubit to another using entanglement and classical communication.

## Overview

The script teleports an arbitrary quantum state |ψ⟩ = (1/√2)(|0⟩ + i|1⟩) from one qubit (Alice) to another qubit (Bob) using:
- An entangled Bell pair shared between Alice and Bob
- Bell measurement by Alice
- Conditional corrections applied by Bob based on Alice's measurement results

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Script

```bash
python3 quantum_teleportation.py
```

## What the Script Does

1. **Prepares the initial state**: Creates a superposition state (1/√2)(|0⟩ + i|1⟩) using Hadamard (H) and S gates
2. **Creates entanglement**: Generates a Bell pair between Alice's second qubit and Bob's qubit
3. **Performs Bell measurement**: Alice entangles her state with her half of the Bell pair and measures both qubits
4. **Applies corrections**: Bob applies X and Z gates conditionally based on Alice's measurement results
5. **Verifies teleportation**: Measures Bob's qubit and compares the distribution with the original state

## Expected Results

The script outputs:
- The initial statevector to be teleported
- A visual representation of the quantum circuit
- Measurement counts from the simulation (1024 shots)
- Distribution of the teleported qubit measurements
- Two plots (if display is available):
  - Histogram of teleported qubit measurements
  - Bloch sphere visualization of the initial state

The teleported qubit should show approximately 50/50 distribution between |0⟩ and |1⟩, matching the probability distribution of the initial state.

## Circuit Structure

```
q0 (Alice's state): Initial state → Bell measurement → Measure
q1 (Alice's Bell):  Bell pair creation → Bell measurement → Measure  
q2 (Bob's Bell):    Bell pair creation → Corrections → Final measurement
```

## Key Concepts

- **Quantum Entanglement**: q1 and q2 are entangled in a Bell state
- **Bell Measurement**: Alice measures q0 and q1 in the Bell basis
- **Classical Communication**: Measurement results are sent to Bob (represented by classical bits)
- **Conditional Operations**: Bob applies X and Z gates based on measurement outcomes
- **No-Cloning**: The original state on q0 is destroyed during measurement (no copying)

## Notes

- The script uses the Aer simulator for quantum circuit simulation
- Plots require a display environment; use `MPLBACKEND=Agg` for headless environments
- The teleportation preserves the quantum state distribution but not individual measurement outcomes
