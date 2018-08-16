import numpy as np

from squanch import linalg

__all__ = ["H", "X", "Y", "Z", "RX", "RY", "RZ", "PHASE", "CNOT", "TOFFOLI", "CU", "CPHASE", "SWAP", "expand"]

# Single qubit operators that can be applied with qubit.apply()

# Projection operators
_M0 = np.outer([1, 0],
               [1, 0])
_M1 = np.outer([0, 1],
               [0, 1])

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
    ``cache_id``: ``H``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.apply(_H, id = "H")


def X(qubit):
    '''
    Applies the Pauli-X (NOT) operation to the specified qubit, updating the qsystem state.
    ``cache_id``: ``X``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.apply(_X, id = "X")


def Y(qubit):
    '''
    Applies the Pauli-Y operation to the specified qubit, updating the qsystem state.
    ``cache_id``: ``Y``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.apply(_Y, id = "Y")


def Z(qubit):
    '''
    Applies the Pauli-Z operation to the specified qubit, updating the qsystem state.
    ``cache_id``: ``Z``

    :param Qubit qubit: the qubit to apply the operator to
    '''
    qubit.apply(_Z, id = "Z")


def RX(qubit, angle):
    '''
    Applies the single qubit X-rotation operator to the specified qubit, updating the qsystem state.
    ``cache_id``: ``Rx*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _X
    qubit.apply(gate, id = "Rx" + str(angle / np.pi))


def RY(qubit, angle):
    '''
    Applies the single qubit Y-rotation operator to the specified qubit, updating the qsystem state.
    ``cache_id``: ``Ry*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _Y
    qubit.apply(gate, id = "Ry" + str(angle / np.pi))


def RZ(qubit, angle):
    '''
    Applies the single qubit Z-rotation operator to the specified qubit, updating the qsystem state.
    ``cache_id``: ``Rz*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the angle by which to rotate
    '''
    gate = np.cos(angle / 2.0) * _I - 1j * np.sin(angle / 2.0) * _Z
    qubit.apply(gate, id = "Rz" + str(angle / np.pi))


def PHASE(qubit, angle):
    '''
    Applies the phase operation from control on target, mapping |1> to e^(i*angle)|1>.
    ``cache_id``: ``PHASE*``, where * is angle/pi

    :param Qubit qubit: the qubit to apply the operator to
    :param float angle: the phase angle to apply
    '''
    gate = np.array([[1, 0], [0, np.exp(1j * angle)]])
    qubit.apply(gate, id = "PHASE" + str(angle / np.pi))


def CNOT(control, target):
    '''
    Applies the controlled-NOT operation from control on target. This gate takes two qubit arguments to
    construct an arbitrary CNOT matrix.
    ``cache_id``: ``CNOTi,j,N``, where i and j are control and target indices and N is num_qubits

    :param Qubit control: the control qubit
    :param Qubit target: the target qubit, with Pauli-X applied according to the control qubit
    '''
    num_qubits = target.qsystem.num_qubits
    key = "CNOT" + str(control.index) + "," + str(target.index) + "," + str(num_qubits)
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


def CU(control, target, unitary):
    '''
    Applies the controlled-unitary operation from control on target. This gate takes control and target qubit arguments
    and a unitary operator to apply
    ``cache_id``: ``CUi,j,<str(unitary)>,N``, where i and j are control and target indices and N is num_qubits

    :param Qubit control: the control qubit
    :param Qubit target: the target qubit
    :param np.array unitary: the unitary single-qubit gate to apply to the target qubit
    '''
    num_qubits = target.qsystem.num_qubits
    key = "CU" + str(control.index) + "," + str(target.index) + "," + str(unitary) + "," + str(num_qubits)
    # Generate the gate if needed
    if key not in _expandedGateCache:
        # Represent CNOT(i,j) as |0i><0i| x I x ... x I + |1i><1i| x I x ... x Xtarg x I x ...
        proj0 = linalg.tensor_fill_identity(_M0, control.qsystem.num_qubits, control.index)
        proj1gates = [_I for _ in range(control.qsystem.num_qubits)]
        proj1gates[control.index] = _M1
        proj1gates[target.index] = unitary
        proj1 = linalg.tensors(proj1gates)
        CUij = proj0 + proj1
        # Cache the gate
        _expandedGateCache[key] = CUij
    # Apply the gate
    target.qsystem.apply(_expandedGateCache[key])


def CPHASE(control, target, angle):
    '''
    Applies the controlled-phase operation from control on target. This gate takes control and target qubit arguments
    and a rotation angle, and calls CU(control, target, np.array([[1, 0], [0, np.exp(1j * angle)]])).

    :param Qubit control: the control qubit
    :param Qubit target: the target qubit
    :param float angle: the phase angle to apply
    '''
    matrix = np.array([[1, 0], [0, np.exp(1j * angle)]])
    CU(control, target, matrix)


def TOFFOLI(control1, control2, target):
    '''
    Applies the Toffoli (or controlled-controlled-NOT) operation from control on target. This gate takes three qubit
    arguments to construct an arbitrary CCNOT matrix.
    ``cache_id``: ``CCNOTi,j,k,N``, where i and j are control indices and k target indices and N is num_qubits

    :param Qubit control1: the first control qubit
    :param Qubit control2: the second control qubit
    :param Qubit target: the target qubit, with Pauli-X applied according to the control qubit
    '''
    c1, c2 = sorted([control1.index, control2.index])
    num_qubits = target.qsystem.num_qubits
    key = "CCNOT" + str(c1) + "," + str(c2) + "," + str(target.index) + "," + str(num_qubits)
    # Generate the gate if needed
    if key not in _expandedGateCache:
        gates_list = [[_M0, _M0, _I], [_M0, _M1, _I], [_M1, _M0, _I], [_M1, _M1, _X]]
        CNOTijk = 0
        for gates in gates_list:
            ops = [_I for _ in range(num_qubits)]
            ops[c1] = gates[0]
            ops[c2] = gates[1]
            ops[target.index] = gates[2]
            operator = linalg.tensors(ops)
            CNOTijk += operator
        # Cache the gate
        _expandedGateCache[key] = CNOTijk
    # Apply the gate
    target.qsystem.apply(_expandedGateCache[key])


def SWAP(q1, q2):
    '''
    Applies the SWAP operator to two qubits, switching the states. This gate is implemented by three CNOT operations 
    and thus has no ``cache_id``.
    :param q1: the first qubit
    :param q2: the second qubit
    '''
    CNOT(q2, q1)
    CNOT(q1, q2)
    CNOT(q2, q1)


_expandedGateCache = {}


def expand(operator, index, num_qubits, cache_id = None):
    '''
    Apply a k-qubit quantum gate to act on n-qubits by filling the rest of the spaces with identity operators

    :param np.array operator: the single- or n-qubit operator to apply
    :param int index: if specified, the index of the qubit to perform the operation on
    :param int num_qubits: the number of qubits in the system
    :param str ``cache_id``: a character identifier to cache gates and their expansions in memory
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
