import numpy as np
import qubit, linalg


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
        self.systemSize = systemSize  # number of qubits per system
        # Initialize each qubit state
        zero = np.array([1, 0], dtype = np.complex64)  # vector representation of the |0> pure state
        initialQubitState = np.outer(zero, zero)  # each qubit is initialized as |0><0|
        initialSystemState = np.array([], dtype = np.complex64)
        # Generate the matrix representation of the initial state of the n-qubit system
        for _ in range(systemSize):
            initialSystemState = linalg.tensorProd(initialSystemState, initialQubitState)

        # Generate the matrix representation of the overall state of the quantum stream
        # The Hilbert space of QSys0 x QSys1 x ... x QSysN is represented as an n-dimensional array of state vectors
        self.state = np.repeat([initialSystemState], numSystems, axis = 0)  # repeat system state into vertical axis

        # The "head" of the stream; what qSystem is being processed at the moment
        self.index = 0

    def system(self, index):
        '''
        Access the nth quantum system in the quantum datastream object
        :param index: zero-index of the quantum system to access
        :return: the state vector of the quantum system
        '''
        return qubit.QSystem(self.systemSize, self.state[index])

    def head(self):
        '''
        Access the "head" of the quantum system "queue", returning it as a QSystem object, and increment the head by 1
        :return: a QSystem for the "head" system
        '''
        sys = self.system(self.index)
        self.index += 1
        return sys

