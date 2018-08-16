import numpy as np

from squanch import linalg, gates

__all__ = ["QSystem", "Qubit"]

# Computational basis and projection operators
_0 = np.array([1, 0], dtype = np.complex64)
_1 = np.array([0, 1], dtype = np.complex64)
_M0 = np.outer(_0, _0)
_M1 = np.outer(_1, _1)


class QSystem:
    '''
    Represents a multi-body, maximally-entangleable quantum system. Contains references to constituent qubits and
    (if applicable) its parent ``QStream``. Quantum state is represented as a density matrix in the computational basis.
    '''

    def __init__(self, num_qubits, index = None, state = None):
        '''
        Instatiate the quantum state for an n-qubit system

        :param int num_qubits: number of qubits in the system, treated as maximally entangled
        :param int index: index of the QSystem within the parent QStream
        :param np.array state: density matrix representing the quantum state. By default, |000...0><0...000| is used
        '''
        self.num_qubits = num_qubits
        self.qubits = (Qubit(self, i) for i in range(num_qubits))  # this is a generator, not a list
        self.index = index
        # Register the state or generate a new one
        if state is not None:
            self.state = state  # density matrix should be passed by reference and will modify the QStream.state
        else:
            # Initialize each qubit state
            initial_qubit_state = np.outer(_0, _0)  # each qubit is initialized as |0><0|
            initial_system_state = np.array([], dtype = np.complex64)
            # Generate the matrix representation of the initial state of the n-qubit system
            for _ in range(self.num_qubits):
                initial_system_state = linalg.tensor_product(initial_system_state, initial_qubit_state)
            # Assign the state
            self.state = initial_system_state

    @classmethod
    def from_stream(cls, qstream, index):
        '''
        Instantiate a QSystem from a given index in a parent QStream

        :param QStream qstream: the parent stream
        :param int index: the index in the parent stream corresponding to this system
        :return: the QSystem object
        '''
        return cls(qstream.system_size, index = index, state = qstream.state[index])

    def qubit(self, index):
        '''
        Access a qubit by index; self.qubits does not instantiate all qubits unless casted to a list. Use this
        function to access a single qubit of a given index.

        :param int index: qubit index to generate a qubit instance for
        :return: the qubit instance
        '''
        return Qubit(self, index)

    def measure_qubit(self, index):
        '''
        Measure the qubit at a given index, partially collapsing the state based on the observed qubit value.
        The state vector is modified in-place by this function.

        :param int index: the qubit to measure
        :return: the measured qubit value
        '''
        measure0 = gates.expand(_M0, index, self.num_qubits, "0" + str(index) + str(self.num_qubits))
        prob0 = np.trace(np.dot(measure0, self.state))
        # Determine if qubit collapses to |0> or |1>
        if np.random.rand() <= prob0:
            # qubit collapses to |0>
            self.state[...] = np.linalg.multi_dot([measure0, self.state, measure0.conj().T]) / prob0
            return 0
        else:
            # qubit collapses to |1>
            measure1 = gates.expand(_M1, index, self.num_qubits, "1" + str(self.num_qubits))
            self.state[...] = np.linalg.multi_dot([measure1, self.state, measure1]) / (1.0 - prob0)
            return 1

    def apply(self, operator):
        '''
        Apply an N-qubit unitary operator to this system's N-qubit quantum state

        :param np.array operator: the unitary N-qubit operator to apply
        :return: nothing, the qsystem state is mutated
        '''
        # Apply the operator
        # assert linalg.isHermitian(operator), "Qubit operators must be Hermitian"
        self.state[...] = np.linalg.multi_dot([operator, self.state, operator.conj().T])
        # self.state[...] = np.linalg.multi_dot([operator, self.state, operator])


class Qubit:
    '''
    A wrapper class representing a single qubit in an existing quantum system.
    '''

    def __init__(self, qsystem, index):
        '''
        Instantiate the qubit from an existing QSystem and index

        :param QSystem qsystem: n-qubit quantum system that this qubit points to
        :param int index: particle index in the quantum system, ranging from 0 to n-1
        '''
        self.index = index
        self.qsystem = qsystem

    @classmethod
    def from_stream(cls, qstream, system_index, qubit_index):
        '''
        Instantiate a qubit from a parent stream (via a QSystem call)

        :param QStream qstream: the parent stream
        :param int system_index: the index corresponding to the parent QSystem
        :param int qubit_index: the index of the qubit to be recalled
        :return: the qubit
        '''
        return qstream.system(system_index).qubit(qubit_index)

    def measure(self):
        '''
        Measure a qubit, modifying the density matrix of its parent ``QSystem`` in-place

        :return: the measured value
        '''
        return self.qsystem.measure_qubit(self.index)

    def apply(self, operator, id = None):
        '''
        Apply a single-qubit operator to this qubit, tensoring with I and passing to the qsystem.apply() method

        :param np.array operator: a single qubit (2x2) complex-valued matrix
        :param str cacheID: a character or string to cache the expanded operator by (e.g. Hadamard qubit 2 -> "IHII...")
        '''
        self.qsystem.apply(gates.expand(operator, self.index, self.qsystem.num_qubits, id))

    def serialize(self):
        '''
        Generate a reference to reconstruct this qubit from shared memory

        :return: qubit reference as (systemIndex, qubitIndex)
        '''
        return self.qsystem.index, self.index
