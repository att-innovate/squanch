import numpy as np
import linalg  # useful custom linear algebra functions


class Qubit:
    '''
    Simple qubit implementation.
    Retains a reference to a quantum system that can deal with multi-particle dynamics
    '''

    def __init__(self, initialState=np.array([1, 0])):
        self.initialState = initialState  # start off in the |0> state by default
        self.index = 0  # the index/qubit number in the quantum system object
        self.qSystem = QubitSystem([self])  # the overall quantum state of the system of qubits

    def entangle(self, qSystem):
        '''
        Entangle this qubit with another set of ones.
        This doesn't actually perform any entanglement, it just links the quantum systems
        together, allowing multi-particle gates like CNOT to be applied.
        :param qSystem: the state of 1+ qubits with which to entangle this one
        :return: nothing
        '''
        qSystem.addQubit(self)  # add this to the quantum system
        self.qSystem = qSystem  # change the quantum system object

    def measure(self):
        '''
        Perform a measurement in the computational (z) basis on this qubit and update the
        :return: 0 or 1, depending on the outcome of the measurement
        '''
        return self.qSystem.measureQubit(self.index)

    def apply(self, operator):
        '''
        Apply a single-qubit operator to this qubit, updating the overall qSystem
        :param operator: single-qubit operator to apply
        :return: nothing, the qSystem state is mutated
        '''
        self.qSystem.apply(operator, index=self.index)


class QubitSystem:
    '''
    Maintains a multi-particle Hilbert space for several qubits
    '''

    def __init__(self, qubitList):
        '''
        Instantiate a new quantum system object form a list of existing qubits
        :param qubitList: list of qubits to create the state from
        '''
        self.qubits = qubitList
        self.state = []
        for i, qubit in enumerate(qubitList):
            self.state = linalg.tensorProd(self.state, qubit.initialState)
            qubit.index = i

    def addQubit(self, newQubit):
        newQubit.index = len(self.qubits)  # zero indexed, so length is next index
        self.qubits.append(newQubit)
        # TODO: at the moment you can't make modifications to qubits then entangle them
        self.state = linalg.tensorProd(self.state, newQubit.initialState)

    def measureQubit(self, qubitIndex):
        '''
        Measure the qubit at a given index, partially collapsing the state based
        on the observed value of the measured qubit
        :param qubitIndex: the qubit to measure
        :return: the measured qubit value
        '''
        # Generate measurement operators for the n-qubit state
        M0 = np.outer([1, 0], [1, 0])
        M1 = np.outer([0, 1], [0, 1])
        measure0 = linalg.tensorFillIdentity(M0, len(self.qubits), qubitIndex)
        measure1 = linalg.tensorFillIdentity(M1, len(self.qubits), qubitIndex)
        prob0 = np.linalg.multi_dot([
            self.state.conj().T,
            measure0.conj().T,
            measure0,
            self.state
        ])
        prob1 = np.linalg.multi_dot([
            self.state.conj().T,
            measure1.conj().T,
            measure1,
            self.state
        ])
        # Perform the measurement and collapse the state matrix accordingly
        if (np.random.rand() / (prob0 + prob1)) > prob0:
            # qubit collapses to 1
            self.state = np.dot(measure1, self.state) / np.sqrt(prob1)
            return 1
        else:
            # qubit collapses to 0
            self.state = np.dot(measure0, self.state) / np.sqrt(prob0)
            return 0

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
            operator = linalg.tensorFillIdentity(operator, len(self.qubits), index)
        # Apply the operator
        assert linalg.isHermitian(operator), "Qubit operators must be Hermitian"
        self.state = np.dot(operator, self.state)
