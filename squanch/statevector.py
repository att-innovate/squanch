import numpy as np
import linalg
import gates

# Cached projection operators
_M0 = np.outer([1, 0], [1, 0])
_M1 = np.outer([0, 1], [0, 1])


def collapse(rho, qubitIndex, numQubits):
    '''
    Partially collapses the density matrix rho with a projection of indexed qubit onto the computational basis
    :param rho: 2^n dimensional state vector as a numpy array
    :param qubitIndex: index of qubit to project onto the computational basis
    :return: 0 or 1, with probability <psi|0><0|psi> and <psi|1><1|psi>, respectively, modifying |psi> in-place
    '''
    # # Number of qubits in the state vector
    # numQubits = np.log2(rho.size)
    #
    # # Faster cached behavior in the 2-qubit case
    # if numQubits == 2:
    #     return _twoQubitCollapse(rho, qubitIndex)

    # The general (n>2) case
    measure0 = gates.expandGate(_M0, qubitIndex, numQubits, "0") #linalg.tensorFillIdentity(_M0, numQubits, qubitIndex)
    # prob0 = np.linalg.multi_dot([
    #     rho.conj().T,
    #     measure0.conj().T,
    #     measure0,
    #     rho])
    prob0 = np.trace(np.dot(measure0, rho))

    # Determine if qubit collapses to |0> or |1>
    if np.random.rand() <= prob0:
        # qubit collapses to |0>
        #rho[...] = np.dot(measure0, rho) / np.sqrt(prob0)
        rho[...] = np.linalg.multi_dot([measure0, rho, measure0]) / prob0
        return 0
    else:
        # qubit collapses to |1>
        measure1 = gates.expandGate(_M1, qubitIndex, numQubits, "1")
        # measure1 = linalg.tensorFillIdentity(_M0, numQubits, qubitIndex)
        #rho[...] = np.dot(measure1, rho) / np.sqrt(1 - prob0)
        rho[...] = np.linalg.multi_dot([measure1, rho, measure1]) / (1.0 - prob0)
        return 1


# # Cached 2-qubit operators to avoid recalculation in common usage cases
# _twoQubitMeasure0q0 = np.dot(linalg.tensorFillIdentity(_M0, 2, 0).conj().T, linalg.tensorFillIdentity(_M0, 2, 0))
# _twoQubitMeasure0q1 = np.dot(linalg.tensorFillIdentity(_M0, 2, 1).conj().T, linalg.tensorFillIdentity(_M0, 2, 1))
# _twoQubitMeasure1q0 = np.dot(linalg.tensorFillIdentity(_M1, 2, 0).conj().T, linalg.tensorFillIdentity(_M1, 2, 0))
# _twoQubitMeasure1q1 = np.dot(linalg.tensorFillIdentity(_M1, 2, 1).conj().T, linalg.tensorFillIdentity(_M1, 2, 1))
#
# # Non-projective form of these operators for <psi|0><0|psi> -> (<0|psi>)^2
# _bra0q0 = linalg.tensorProd([1, 0], [1, 1])
# _bra0q1 = linalg.tensorProd([1, 1], [1, 0])
# _bra1q0 = linalg.tensorProd([0, 1], [1, 1])
# _bra1q1 = linalg.tensorProd([1, 1], [0, 1])
#
#
# def _twoQubitCollapse(psi, qubitIndex):
#     '''
#     Optimized version of collapse() for the 2-qubit case
#     :param psi: 2^n dimensional state vector as a numpy array
#     :param qubitIndex: index of qubit to project onto the computational basis
#     :return: 0 or 1, with probability <psi|0><0|psi> and <psi|1><1|psi>, respectively, modifying |psi> in-place
#     '''
#     if qubitIndex == 0:
#         dot = np.dot(_bra0q0, psi)
#         prob0 = dot.real ** 2 + dot.imag ** 2
#         if np.random.rand() <= prob0:
#             # qubit collapses to |0>
#             psi[...] = np.dot(_twoQubitMeasure0q0, psi) / np.sqrt(prob0)
#             return 0
#         else:
#             # qubit collapses to |1>
#             psi[...] = np.dot(_twoQubitMeasure1q0, psi) / np.sqrt(1 - prob0)
#             return 1
#
#     else:
#         dot = np.dot(_bra0q1, psi)
#         prob0 = dot.real ** 2 + dot.imag ** 2
#         if np.random.rand() <= prob0:
#             # qubit collapses to |0>
#             psi[...] = np.dot(_twoQubitMeasure0q1, psi) / np.sqrt(prob0)
#             return 0
#         else:
#             # qubit collapses to |1>
#             psi[...] = np.dot(_twoQubitMeasure1q1, psi) / np.sqrt(1 - prob0)
#             return 1

# def _twoQubitCollapse(psi, qubitIndex):
#     '''
#     Optimized version of collapse() for the 2-qubit case
#     :param psi: 2^n dimensional state vector as a numpy array
#     :param qubitIndex: index of qubit to project onto the computational basis
#     :return: 0 or 1, with probability <psi|0><0|psi> and <psi|1><1|psi>, respectively, modifying |psi> in-place
#     '''
#     if qubitIndex == 0:
#         prob0 = np.linalg.multi_dot([psi.conj().T,
#                                      _twoQubitMeasure0q0,
#                                      psi])
#         if np.random.rand() <= prob0:
#             # qubit collapses to |0>
#             psi[...] = np.dot(_twoQubitMeasure0q0, psi) / np.sqrt(prob0)
#             return 0
#         else:
#             # qubit collapses to |1>
#             psi[...] = np.dot(_twoQubitMeasure1q0, psi) / np.sqrt(1 - prob0)
#             return 1
#
#     else:
#         prob0 = np.linalg.multi_dot([psi.conj().T,
#                                      _twoQubitMeasure0q1,
#                                      psi])
#         if np.random.rand() <= prob0:
#             # qubit collapses to |0>
#             psi[...] = np.dot(_twoQubitMeasure0q1, psi) / np.sqrt(prob0)
#             return 0
#         else:
#             # qubit collapses to |1>
#             psi[...] = np.dot(_twoQubitMeasure1q1, psi) / np.sqrt(1 - prob0)
#             return 1
