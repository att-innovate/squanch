import sys
import numpy as np
import multiprocessing
from qubit import Qubit
import errors


class QChannel:
    '''
    Base class for a quantum channel
    '''

    def __init__(self, fromAgent, toAgent, length = 0.0, errors = []):
        '''
        Instantiate the quantum channel

        :param Agent fromAgent: sending agent
        :param Agent toAgent: receiving agent
        :param float length: length of quantum channel in km; default: 0.0km
        :param QError[] errors: list of error models to apply to qubits in this channel; default: [] (no errors)
        '''
        # Register agent connections
        self.fromAgent = fromAgent
        self.toAgent = toAgent

        # Signal propagation properties
        self.length = length  # Physical length of the channel in km
        self.signalSpeed = 2.998 * 10 ** 5  # Speed of light in km/s

        # A queue representing the qubits in transit along the channel
        self.queue = multiprocessing.Queue()

        # Register error models
        self.errors = errors

    def put(self, qubit):
        '''
        Serialize and push qubit into the channel queue

        :param Qubit qubit: the qubit to send
        '''
        # Calculate the time of arrival
        timeOfArrival = self.fromAgent.time + self.fromAgent.pulseLength + (self.length / self.signalSpeed)
        if qubit is not None:
            self.queue.put((qubit.serialize(), timeOfArrival))
        else:
            self.queue.put((None, timeOfArrival))

    def get(self):
        '''
        Retrieve a qubit by reference from the channel queue, applying errors upon retrieval

        :return: tuple: (the qubit with errors applied (possibly ``None``), receival time)
        '''
        indices, receiveTime = self.queue.get()
        if indices is not None:
            systemIndex, qubitIndex = indices
            qubit = Qubit.fromStream(self.toAgent.stream, systemIndex, qubitIndex)
        else:
            qubit = None

        # Apply errors
        for error in self.errors:
            qubit = error.apply(qubit)

        # Return modified qubit and return time
        return qubit, receiveTime


class CChannel:
    '''
    Base class for a classical channel
    '''

    def __init__(self, fromAgent, toAgent, length = 0.0):
        '''
        Instantiate the quantum channel

        :param Agent fromAgent: sending agent
        :param Agent toAgent: receiving agent
        :param float length: length of fiber optic line in km; default: 0.0km
        '''
        # Register agent connections
        self.fromAgent = fromAgent
        self.toAgent = toAgent

        # Signal propagation
        self.length = length  # Physical length of the channel in km
        self.signalSpeed = 2.998 * 10 ** 5  # Speed of light in km/s

        # The channel queue
        self.queue = multiprocessing.Queue()

    def put(self, thing):
        '''
        Serialize and push a serializable object into the channel queue

        :param any thing: the qubit to send
        '''
        # Calculate the time of arrival
        pulseTime = sys.getsizeof(thing) * 8 * self.fromAgent.pulseLength
        timeOfArrival = self.fromAgent.time + pulseTime + (self.length / self.signalSpeed)
        self.queue.put((thing, timeOfArrival))

    def get(self):
        '''
        Retrieve a classical object form the queue

        :return: tuple: (the object, receival time)
        '''
        thing, receiveTime = self.queue.get()
        return thing, receiveTime


class FiberOpticQChannel(QChannel):
    '''
    Represents a fiber optic line with attenuation errors
    '''

    def __init__(self, fromAgent, toAgent, length = 0.0):
        '''
        Instantiate the simulated fiber optic quantum channel

        :param Agent fromAgent: sending agent
        :param Agent toAgent: receiving agent
        :param float length: length of fiber optic channel in km; default: 0.0km
        '''
        QChannel.__init__(self, fromAgent, toAgent, length = length)

        # Register attenuation errors
        self.errors = [
            errors.AttenuationError(self),
            # errors.RandomUnitaryError(self, 2*np.pi / 100),
            # errors.SystematicUnitaryError(self, 2*np.pi / 10),
        ]
