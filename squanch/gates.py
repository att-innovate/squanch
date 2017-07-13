import numpy as np
import linalg

# Single qubit operators that can be applied with qubit.apply()

# Identity operator
_I = np.array([[1, 0],
               [0, 1]])

# Hadamard gate
_H = 1 / np.sqrt(2) * np.array([[1, 1],
                                [1, -1]])

# Pauli-X gate (bit flip)
_X = np.array([[0, 1],
               [1, 0]])

# Pauli-Y gate (bit + phase flip)
_Y = np.array([[0, -1j],
               [1j, 0]])

# Pauli-Z gate (phase flip)
_Z = np.array([[1, 0],
               [0, -1]])


# Single qubit gates
def H(qubit):
    '''
    Implements the Hadamard transform on a given qubit, updating the qSystem
    :param qubit: the qubit to apply the operator to
    :return: nothing - the qSystem is mutated by this function
    '''
    qubit.qSystem.apply(expandGate(_H, qubit.index, qubit.qSystem.numQubits, "H"))


def X(qubit):
    qubit.qSystem.apply(expandGate(_X, qubit.index, qubit.qSystem.numQubits, "X"))


def Y(qubit):
    qubit.qSystem.apply(expandGate(_Y, qubit.index, qubit.qSystem.numQubits, "Y"))


def Z(qubit):
    qubit.qSystem.apply(expandGate(_Z, qubit.index, qubit.qSystem.numQubits, "Z"))


# Controlled-not gate
_CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
])

_SWAP = np.array([
    [1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
])

_expandedGateCache = {}

def expandGate(operator, index, nQubits, cacheID=None):
    '''
    Apply a k-qubit quantum gate to act on n-qubits by filling the rest of the spaces with identity operators
    :param operator: the single- or n-qubit operator to apply
    :param index: if specified, the index of the qubit to perform the operation on
    :param nQubits: the number of qubits in the system
    :param cacheID: a character identifier to cache common gates in memory to avoid having to call tensorFillIdentity
    :return: nothing, the qSystem state is mutated
    '''

    if cacheID is not None:
        key = "I" * index + cacheID + "I" * (nQubits - 1 - index)
        if key not in _expandedGateCache: # cache the expanded gate
            expandedOperator = linalg.tensorFillIdentity(operator, nQubits, index)
            _expandedGateCache[key] = expandedOperator
        return _expandedGateCache[key]
    else:
        return linalg.tensorFillIdentity(operator, nQubits, index)
