import numpy as np
import qubit, linalg
import ctypes
from multiprocessing import sharedctypes


def allZeroState(systemSize, numSystems):
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
        :param systemSize: number of entangled qubits in each quantum system; each system has dimension 2^systemSize
        :param numSystems: number of small quantum systems in the data stream
        :param array: pre-allocated array in memory for purposes of sharing QStreams in multiprocessed environments
        '''
        self.systemSize = systemSize  # number of qubits per system

        # Generate the matrix representation of the overall state of the quantum stream
        if array is not None:
            self.state = array
        else:
            self.state = allZeroState(systemSize, numSystems)

        # The "head" of the stream; what qSystem is being processed at the moment
        self.index = 0

    @classmethod
    def fromArray(cls, array, reformatArray = False):
        '''
        Instantiates a quantum datastream object from a (typically shared) pre-allocated array
        :param array:
        :param reformatArray: if providing a pre-allocated array, whether to reformat it to the all-zero state
        :return:
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
        :param array: a numSystems x 2^systemSize x 2^systemSize array of np.complex64 values
        :return: nothing, operations are done in place
        '''
        numSystems = array.shape[0]
        systemSize = int(np.log2(array.shape[1]))
        array[...] = allZeroState(systemSize, numSystems)

    @staticmethod
    def generateSharedHilbertSpace(systemSize, numSystems):
        '''
        Allocate a portion of shareable c-type memory to create a numpy array that is sharable between processes
        :param systemSize: number of entangled qubits in each quantum system; each system has dimension 2^systemSize
        :param numSystems: number of small quantum systems in the data stream
        :return: a blank, sharable, numSystems x 2^systemSize x 2^systemSize array of np.complex64 values
        '''
        dim = 2 ** systemSize
        shared_mem = sharedctypes.RawArray(ctypes.c_double, numSystems * dim * dim)
        array = np.frombuffer(shared_mem, dtype = np.complex64).reshape((numSystems, dim, dim))
        QStream.reformatArray(array)
        return array

    def system(self, index):
        '''
        Access the nth quantum system in the quantum datastream object
        :param index: zero-index of the quantum system to access
        :return: the state vector of the quantum system
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
