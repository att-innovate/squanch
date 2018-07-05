import numpy as np
from squanch import linalg

__all__ = ["H", "X", "Y", "Z", "RX", "RY", "RZ", "CNOT", "expand"]

# Single qubit operators that can be applied with qubit.apply()

# Projection operators
_M0 = np.outer([1, 0], [1, 0])
_M1 = np.outer([0, 1], [0, 1])

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
    Applies the Hadamard transform to the specified qubit, updating the qsystem state.
    cacheID: ``H``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.qsystem.apply(expand(_H, qubit.index, qubit.qsystem.num_qubits, "H"))


def X(qubit):
    '''
    Applies the Pauli-X (NOT) operation to the specified qubit, updating the qsystem state.
    cacheID: ``X``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.qsystem.apply(expand(_X, qubit.index, qubit.qsystem.num_qubits, "X"))


def Y(qubit):
    '''
    Applies the Pauli-Y operation to the specified qubit, updating the qsystem state.
    cacheID: ``Y``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.qsystem.apply(expand(_Y, qubit.index, qubit.qsystem.num_qubits, "Y"))


def Z(qubit):
    '''
    Applies the Pauli-Z operation to the specified qubit, updating the qsystem state.
    cacheID: ``Z``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.qsystem.apply(expand(_Z, qubit.index, qubit.qsystem.num_qubits, "Z"))


def RX(qubit, angle):
    '''
    Applies the single qubit X-rotation operator to the specified qubit, updating the qsystem state.
    cacheID: ``Rx*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _X
    qubit.qsystem.apply(expand(gate, qubit.index, qubit.qsystem.num_qubits, "Rx" + str(angle / np.pi)))


def RY(qubit, angle):
    '''
    Applies the single qubit Y-rotation operator to the specified qubit, updating the qsystem state.
    cacheID: ``Ry*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _Y
    qubit.qsystem.apply(expand(gate, qubit.index, qubit.qsystem.num_qubits, "Ry" + str(angle / np.pi)))


def RZ(qubit, angle):
    '''
    Applies the single qubit Z-rotation operator to the specified qubit, updating the qsystem state.
    cacheID: ``Rz*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _Z
    qubit.qsystem.apply(expand(gate, qubit.index, qubit.qsystem.num_qubits, "Rz" + str(angle / np.pi)))


# Controlled-not gate

def CNOT(control, target):
    '''
    Applies the controlled-NOT operation from control on target. This gate takes two qubit arguments to
    construct an arbitrary CNOT matrix.
    cacheID: ``CNOTij``, where i and j are control and target indices

    :param Qubit control: the control qubit
    :param Qubit target: the target qubit, with Pauli-X applied according to the control qubit
    '''
    key = "CNOT" + str(control.index) + "," + str(target.index)
    # Generate the gate if needed
    if key not in _expandedGateCache:
        # Represent CNOT(i,j) as |0i><0i| x I x ... x I + |1i><1i| x I x ... x Xtarg x I x ...
        proj0 = linalg.tensor_fill_identity(_M0, control.qsystem.num_qubits, control.index)
        proj1gates = [_I for _ in range(control.qsystem.num_qubits)]
        proj1gates[control.index] = _M1
        proj1gates[target.index] = _X
        proj1 = linalg.tensors(proj1gates)
        CNOTij = proj0 + proj1
        # Cache the gate
        _expandedGateCache[key] = CNOTij
    # Apply the gate
    target.qsystem.apply(_expandedGateCache[key])


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


def expand(operator, index, num_qubits, cache_id = None):
    '''
    Apply a k-qubit quantum gate to act on n-qubits by filling the rest of the spaces with identity operators

    :param np.array operator: the single- or n-qubit operator to apply
    :param int index: if specified, the index of the qubit to perform the operation on
    :param int num_qubits: the number of qubits in the system
    :param str cache_id: a character identifier to cache gates and their expansions in memory
    :return: the expanded n-qubit operator
    '''

    if cache_id is not None:
        key = "I" * index + cache_id + "I" * (num_qubits - 1 - index)
        if key not in _expandedGateCache:  # cache the expanded gate
            expandedOperator = linalg.tensor_fill_identity(operator, num_qubits, index)
            _expandedGateCache[key] = expandedOperator
        return _expandedGateCache[key]
    else:
        return linalg.tensor_fill_identity(operator, num_qubits, index)
