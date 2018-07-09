import numpy as np

__all__ = ["is_hermitian", "tensor_product", "tensors", "tensor_fill_identity"]


def is_hermitian(matrix):
    '''
    Checks if an operator is Hermitian

    :param np.array matrix: the operator to check
    :return: true or false
    '''
    return np.array_equal(matrix.conj().T, matrix)


def tensor_product(state1, state2):
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


def tensors(operator_list):
    '''
    Returns the iterated Kronecker product of a list of states

    :param [np.array] operator_list: list of states to tensor-product
    :return: the tensor product
    '''
    result = []
    for operator in operator_list:
        result = tensor_product(result, operator)
    return result


def tensor_fill_identity(single_qubit_operator, n_qubits, qubit_index):
    '''
    Create the n-qubit operator I x I x ... Operator x I x I... with operator applied to a given qubit index

    :param np.array single_qubit_operator: the operator in the computational basis (a 2x2 matrix)
    :param int n_qubits: the number of qubits in the system to fill
    :param int qubit_index: the zero-indexed qubit to apply this operator to
    :return: the n-qubit operator
    '''
    # assert 0 <= qubit_index <= n_qubits - 1, "qubit Index is out of range"
    operator = tensors([
        tensors([np.eye(2)] * qubit_index),
        single_qubit_operator,
        tensors([np.eye(2)] * (n_qubits - (qubit_index + 1)))
    ])
    return operator
