import numpy as np
import linalg  # useful custom linear algebra functions
import gates

# Computational basis and projection operators
_0 = np.array([1, 0], dtype = np.complex64)
_1 = np.array([0, 1], dtype = np.complex64)
_M0 = np.outer(_0, _0)
_M1 = np.outer(_1, _1)


class QSystem:
    '''
    Represents a multi-particle Hilbert space for several qubuts comprising a single system of a quantum datastream.
    Designed to have similar syntax to QubitSytem, but instantiation is much faster
    '''

    def __init__(self, numQubits, index = None, state = None):
        '''
        Instatiate the quantum state for an n-qubit system
        :param numQubits: number of qubits in the system, treated as maximally entangled
        :param state: density matrix representing the quantum state. If none is provided, |000...><...000| is used
        '''
        self.numQubits = numQubits
        self.qubits = (Qubit(self, i) for i in range(numQubits)) # this is a generator, not a list
        self.index = index
        # Register the state or generate a new one
        if state is not None:
            self.state = state  # density matrix should be passed by reference and will modiy the QStream.state
        else:
            # Initialize each qubit state
            initialQubitState = np.outer(_0, _0)  # each qubit is initialized as |0><0|
            initialSystemState = np.array([], dtype = np.complex64)
            # Generate the matrix representation of the initial state of the n-qubit system
            for _ in range(self.numQubits):
                initialSystemState = linalg.tensorProd(initialSystemState, initialQubitState)
            # Assign the state
            self.state = initialSystemState

    @classmethod
    def fromStream(cls, qStream, systemIndex):
        return cls(qStream.systemSize, index = systemIndex, state = qStream.state[systemIndex])

    def qubit(self, qubitIndex):
        '''
        Access a qubit by index; self.qubits does not instantiate all qubits unless casted to a list. Use this
        function to access a single qubit of a given index.
        :param index: qubit index to generate a qubit instance for
        :return: the qubit instance
        '''
        return Qubit(self, qubitIndex)

    def measureQubit(self, qubitIndex):
        '''
        Measure the qubit at a given index, partially collapsing the state based on the observed qubit value.
        The state vector is modified in-place by this function
        :param qubitIndex: the qubit to measure
        :return: the measured qubit value
        '''
        measure0 = gates.expandGate(_M0, qubitIndex, self.numQubits, "0")
        prob0 = np.trace(np.dot(measure0, self.state))
        # Determine if qubit collapses to |0> or |1>
        if np.random.rand() <= prob0:
            # qubit collapses to |0>
            self.state[...] = np.linalg.multi_dot([measure0, self.state, measure0]) / prob0
            return 0
        else:
            # qubit collapses to |1>
            measure1 = gates.expandGate(_M1, qubitIndex, self.numQubits, "1")
            self.state[...] = np.linalg.multi_dot([measure1, self.state, measure1]) / (1.0 - prob0)
            return 1

    def apply(self, operator):
        '''
        Apply an n-qubit operator to this system's n-qubit quantum state: U|psi><psi|U^+ (U^+ = U for Hermitian)
        :param operator: the *Hermitian* n-qubit operator to apply
        :return: nothing, the qSystem state is mutated
        '''
        # Apply the operator
        # assert linalg.isHermitian(operator), "Qubit operators must be Hermitian"
        # self.state[...] = np.linalg.multi_dot([operator, self.state, operator.conj().T]) TODO: non-Hermitian ops?
        self.state[...] = np.linalg.multi_dot([operator, self.state, operator])


class Qubit:
    '''
    Represents a single physical qubit, which is a wrapper for part of a pre-allocated nonlocal QSystem
    '''

    def __init__(self, qSystem, index):
        '''
        Instantiate the qubit from an existing QSystem and index
        :param qSystem: n-qubit quantum system that this qubit points to
        :param index: particle index in the quantum system, ranging from 0 to n-1
        '''
        self.index = index
        self.qSystem = qSystem

    @classmethod
    def fromStream(cls, qStream, systemIndex, qubitIndex):
        return qStream.system(systemIndex).qubit(qubitIndex)

    def measure(self):
        return self.qSystem.measureQubit(self.index)

    def getState(self):
        '''
        Traces over the remaining portions of the qSystem to return this qubit's state expressed as a density matrix.
        :return: The (mixed) density matrix describing this qubit's state
        '''
        # TODO: partial trace in numpy?
        pass

    def apply(self, operator, cacheID = None):
        '''
        Apply a single-qubit operator to this qubit, tensoring with I and passing to the qSystem.apply() method
        :param operator: a single qubit (2x2) complex-valued matrix
        :param cacheID: a character or string to cache the expanded operator by (e.g. Hadamard qubit 2 -> "IHIII...")
        :return: nothing
        '''
        self.qSystem.apply(gates.expandGate(operator, self.index, self.qSystem.numQubits, cacheID))

    def serialize(self):
        '''
        Generate a reference to reconstruct this qubit from shared memory
        :return: qubit reference as (systemIndex, qubitIndex)
        '''
        return (self.qSystem.index, self.index)