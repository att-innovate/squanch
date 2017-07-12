import numpy as np
import linalg
import statevector


class QStream:
    '''
    Efficiently handle a large number of small entangled quantum systems to avoid having to perform many class
    instantiations when simulating transmission of data through quantum channels
    '''

    def __init__(self, systemSize, numSystems):
        '''
        Instantiate the quantum datastream object
        :param systemSize: number of entangled qubits in each quantum system; each system has dimension 2^systemSize
        :param numSystems: number of small quantum systems in the data stream
        '''
        initialQubitState = np.array([1, 0], dtype=np.complex128)  # each qubit is initialized to the |0> state
        initialSystemState = np.array([], dtype=np.complex128)
        # Generate the matrix representation of the initial state of the n-qubit system
        for _ in range(2):
            initialSystemState = linalg.tensorProd(initialSystemState, initialQubitState)

        # Generate the matrix representation of the overall state of the quantum stream
        # The Hilbert space of QSys0 x QSys1 x ... x QSysN is represented as an n-dimensional array of state vectors
        self.state = np.repeat([initialSystemState], numSystems, axis=0)  # repeat system state into vertical axis

    def system(self, index):
        '''
        Access the nth quantum system in the quantum datastream object
        :param index: zero-index of the quantum system to access
        :return: the state vector of the quantum system
        '''
        return QSystem(self.state[index])


class QSystem:
    '''
    Represents a multi-particle Hilbert space for several qubuts comprising a single system of a quantum datastream.
    Designed to have similar syntax to QubitSytem, but instantiation is much faster
    '''

    def __init__(self, state):
        self.state = state  # state vector should be passed by reference and will modiy the QStream.state
        self.numQubits = int(np.log2(self.state.size))

    def measureQubit(self, qubitIndex):
        '''
        Measure the qubit at a given index, partially collapsing the state based on the observed qubit value.
        The state vector is modified in-place by this function
        :param qubitIndex: the qubit to measure
        :return: the measured qubit value
        '''
        return statevector.collapse(self.state, qubitIndex)

    def apply(self, operator, index=None):
        '''
        Apply an operator to this quantum state. If no index is specified, an n-qubit
        operator is assumed, else a single-qubit operation is applied to the specified
        qubit
        :param operator: the single- or n-qubit operator to apply
        :param index: if specified, the index of the qubit to perform the oepration on
        :return: nothing, the qSystem state is mutated
        '''
        # Expand the operator to n qubits if needed
        if index is not None:
            operator = linalg.tensorFillIdentity(operator, self.numQubits, index)
        # Apply the operator
        # assert linalg.isHermitian(operator), "Qubit operators must be Hermitian"
        self.state[...] = np.dot(operator, self.state)
