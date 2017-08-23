import numpy as np


def isHermitian(matrix):
    '''
    Checks if an operator is Hermitian

    :param np.array matrix: the operator to check
    :return: true or false
    '''
    return np.array_equal(matrix.conj().T, matrix)


def tensorProd(state1, state2):
    '''
    Returns the Kronecker product of two states

    :param np.array state1: the first state
    :param np.array state2: the second state
    :return: the tensor product
    '''
    if len(state1) == 0:
        return state2
    elif len(state2) == 0:
        return state1
    else:
        return np.kron(state1, state2)


def tensors(operatorList):
    '''
    Returns the iterated Kronecker product of a list of states

    :param [np.array] operatorList: list of states to tensor-product
    :return: the tensor product
    '''
    result = []
    for operator in operatorList:
        result = tensorProd(result, operator)
    return result


def tensorFillIdentity(singleQubitOperator, nQubits, qubitIndex):
    '''
    Create the n-qubit operator I x I x ... Operator x I x I... with operator applied to a given qubit index

    :param np.array singleQubitOperator: the operator in the computational basis (a 2x2 matrix)
    :param int nQubits: the number of qubits in the system to fill
    :param int qubitIndex: the zero-indexed qubit to apply this operator to
    :return: the n-qubit operator
    '''
    # assert 0 <= qubitIndex <= nQubits - 1, "qubit Index is out of range"
    operator = tensors([
        tensors([np.eye(2)] * qubitIndex),
        singleQubitOperator,
        tensors([np.eye(2)] * (nQubits - (qubitIndex + 1)))
    ])
    return operator


