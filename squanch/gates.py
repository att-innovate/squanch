import numpy as np

# Single qubit gates
# def Hadamard(qubit):
#     '''
#     Implements the Hadamard transform on a given qubit, updating the qSystem
#     :param qubit: the qubit to apply the operator to
#     :return: nothing - the qSystem is mutated by this function
#     '''
#     hadamardMatrix = 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]])
#     qubit.apply(hadamardMatrix)
#
#
# def PauliX(qubit):
#     xMatrix = np.array([[0, 1], [1, 0]])
#     qubit.apply(xMatrix)
#
#
# def PauliY(qubit):
#     yMatrix = np.array([[0, -1j], [1j, 0]])
#     qubit.apply(yMatrix)
#
#
# def PauliZ(qubit):
#     zMatrix = np.array([[1, 0], [0, -1]])
#     qubit.apply(zMatrix)


# Single qubit operators that can be applied with qubit.apply()

# Identity operator
I = np.array([[1, 0],
              [0, 1]])

# Hadamard gate
H = 1 / np.sqrt(2) * np.array([[1, 1],
                               [1, -1]])

# Pauli-X gate (bit flip)
X = np.array([[0, 1],
              [1, 0]])

# Pauli-Y gate (bit + phase flip)
Y = np.array([[0, -1j],
              [1j, 0]])

# Pauli-Z gate (phase flip)
Z = np.array([[1, 0],
              [0, -1]])

# Some two-qubit operators as matrices; must be applied with qSystem.apply()

# Controlled-not gate; currently must be applied to two adjacent qubits
CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
])
