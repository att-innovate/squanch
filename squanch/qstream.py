import numpy as np
from squanch import qubit, linalg

__all__ = ["QStream"]


def zero_state(system_size, num_systems):
    '''
    Generate an array representing the num_systems Hilbert spaces in the state ``|0>...|0><0|...<0|``

    :param int system_size: maximum size of entangled subsystems
    :param int num_systems: number of disjoint quantum subsystems to allocate
    :return: the all-zero state array
    '''
    # Initialize each qubit state
    zero = np.array([1, 0], dtype = np.complex64)  # vector representation of the |0> pure state
    initial_qubit_state = np.outer(zero, zero)  # each qubit is initialized as |0><0|
    initial_system_state = np.array([], dtype = np.complex64)
    # Generate the matrix representation of the initial state of the n-qubit system
    for _ in range(system_size):
        initial_system_state = linalg.tensor_product(initial_system_state, initial_qubit_state)
    # The Hilbert space of QSys0 x QSys1 x ... x QSysN is represented as an n-dimensional array of state vectors
    return np.repeat([initial_system_state], num_systems, axis = 0)  # repeat state into vertical axis


class QStream:
    '''
    Efficiently handle a large number of small entangled quantum systems to avoid having to perform many class
    instantiations when simulating transmission of data through quantum channels
    '''

    def __init__(self, system_size, num_systems, array = None, agent = None):
        '''
        Instantiate the quantum datastream object

        :param int system_size: number of entangled qubits in each quantum system; each system has dims 2^system_size
        :param int num_systems: number of small quantum systems in the data stream
        :param np.array array: pre-allocated array in memory for purposes of sharing QStreams in multiprocessing
        :param Agent agent: optional reference to the Agent owning the qstream; useful for progress monitoring across
                            separate processes
        '''
        self.system_size = system_size  # number of qubits per system
        self.num_systems = num_systems  # number of disjoint quantum subsystems
        self.agent = agent
        # Generate the matrix representation of the overall state of the quantum stream
        if array is not None:
            self.state = array
        else:
            self.state = zero_state(system_size, num_systems)

        # The "head" of the stream; what qsystem is being processed at the moment
        self.index = 0

    def __iter__(self):
        '''
        Custom iterator method for streams

        :return: each system in the stream
        '''
        for i in range(self.num_systems):
            if self.agent: self.agent.update_progress(i)
            yield self.system(i)

    def __len__(self):
        '''
        Custom length method for streams; equivalent to stream.num_systems

        :return: stream.num_systems
        '''
        return self.num_systems

    @classmethod
    def from_array(cls, array, reformat = False, agent = None):
        '''
        Instantiates a quantum datastream object from a (typically shared) pre-allocated array

        :param np.array array: the pre-allocated np.complex64 array representing the shared Hilbert space
        :param bool reformat: if providing a pre-allocated array, whether to reformat it to the all-zero state
        :return: the child QStream
        '''
        num_systems = array.shape[0]
        system_size = int(np.log2(array.shape[1]))
        qstream = cls(system_size, num_systems, array = array, agent = agent)
        if reformat:
            qstream.reformat(qstream.state)
        return qstream

    @staticmethod
    def reformat(array):
        '''
        Reformats a Hilbert space array in-place to the all-zero state

        :param np.array array: a num_systems x 2^system_size x 2^system_size array of np.complex64 values
        '''
        num_systems = array.shape[0]
        system_size = int(np.log2(array.shape[1]))
        array[...] = zero_state(system_size, num_systems)

    def system(self, index):
        '''
        Access the nth quantum system in the quantum datastream object

        :param int index: zero-index of the quantum system to access
        :return: the quantum system
        '''
        return qubit.QSystem.from_stream(self, index)

    def next(self):
        '''
        Access the next element in the quantum stream, returning it as a QSystem object, and increment the head by 1

        :return: a QSystem for the "head" system
        '''
        sys = self.system(self.index)
        self.index += 1
        return sys
