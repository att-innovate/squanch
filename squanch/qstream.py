import numpy as np
import qubit, linalg



def allZeroState(systemSize, numSystems):
    '''
    Generate an array representing the numSystems Hilbert spaces in the state ``|0>...|0><0|...<0|``

    :param int systemSize: maximum size of entangled subsystems
    :param int numSystems: number of disjoint quantum subsystems to allocate
    :return: the all-zero state array
    '''
    # Initialize each qubit state
    zero = np.array([1, 0], dtype = np.complex64)  # vector representation of the |0> pure state
    initialQubitState = np.outer(zero, zero)  # each qubit is initialized as |0><0|
    initialSystemState = np.array([], dtype = np.complex64)
    # Generate the matrix representation of the initial state of the n-qubit system
    for _ in range(systemSize):
        initialSystemState = linalg.tensorProd(initialSystemState, initialQubitState)
    # The Hilbert space of QSys0 x QSys1 x ... x QSysN is represented as an n-dimensional array of state vectors
    return np.repeat([initialSystemState], numSystems, axis = 0)  # repeat state into vertical axis


class QStream:
    '''
    Efficiently handle a large number of small entangled quantum systems to avoid having to perform many class
    instantiations when simulating transmission of data through quantum channels
    '''

    def __init__(self, systemSize, numSystems, array = None, reformatArray = False):
        '''
        Instantiate the quantum datastream object

        :param int systemSize: number of entangled qubits in each quantum system; each system has dimension 2^systemSize
        :param int numSystems: number of small quantum systems in the data stream
        :param np.array array: pre-allocated array in memory for purposes of sharing QStreams in multiprocessing
        '''
        self.systemSize = systemSize  # number of qubits per system
        self.numSystems = numSystems  # number of disjoint quantum subsystems
        # Generate the matrix representation of the overall state of the quantum stream
        if array is not None:
            self.state = array
        else:
            self.state = allZeroState(systemSize, numSystems)

        # The "head" of the stream; what qSystem is being processed at the moment
        self.index = 0

    def __iter__(self):
        '''
        Custom iterator method for streams

        :return: each system in the stream
        '''
        for i in range(self.numSystems):
            yield self.system(i)

    @classmethod
    def fromArray(cls, array, reformatArray = False):
        '''
        Instantiates a quantum datastream object from a (typically shared) pre-allocated array

        :param np.array array: the pre-allocated np.complex64 array representing the shared Hilbert space
        :param bool reformatArray: if providing a pre-allocated array, whether to reformat it to the all-zero state
        :return: the child QStream
        '''
        numSystems = array.shape[0]
        systemSize = int(np.log2(array.shape[1]))
        qStream = cls(systemSize, numSystems, array = array)
        if reformatArray:
            qStream.reformatArray(qStream.state)
        return qStream

    @staticmethod
    def reformatArray(array):
        '''
        Reformats a Hilbert space array in-place to the all-zero state

        :param np.array array: a numSystems x 2^systemSize x 2^systemSize array of np.complex64 values
        '''
        numSystems = array.shape[0]
        systemSize = int(np.log2(array.shape[1]))
        array[...] = allZeroState(systemSize, numSystems)

    def system(self, index):
        '''
        Access the nth quantum system in the quantum datastream object

        :param int index: zero-index of the quantum system to access
        :return: the quantum system
        '''
        return qubit.QSystem.fromStream(self, index)

    def head(self):
        '''
        Access the "head" of the quantum system "queue", returning it as a QSystem object, and increment the head by 1

        :return: a QSystem for the "head" system
        '''
        sys = self.system(self.index)
        self.index += 1
        return sys
