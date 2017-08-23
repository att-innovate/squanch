import numpy as np
import multiprocessing
from qubit import Qubit

class QChannel:
    '''
    Base class for a quantum channel
    '''

    def __init__(self, length, fromAgent, toAgent):
        '''
        Instantiate the quantum channel

        :param float length: length of fiber optic line
        :param Agent fromAgent: sending agent
        :param Agent toAgent: receiving agent
        '''
        self.length = length # Physical length of the channel in km
        self.signalSpeed = 2.998 * 10**5 # Speed of light in km/s
        self.fromAgent = fromAgent
        self.toAgent = toAgent
        fiberOpticAttenuation = -0.16  # dB/km, from Yin, et al, Satellite-based entanglement
        # Total attenuation along the fiber, equal to probability of receiving a photon
        decibelLoss = self.length * fiberOpticAttenuation
        self.attenuation = 10 ** (decibelLoss / 10)
        # A queue representing the qubits in transit along the channel
        self.queue = multiprocessing.Queue()

    def put(self, qubit):
        '''
        Serialize and push qubit into the channel queue

        :param Qubit qubit: the qubit to send
        :return: nothing
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

        :return: the qubit with errors applied (possibly ``None``)
        '''
        # Don't give the qubit until the required time
        indices, receiveTime = self.queue.get()
        if indices is not None:
            systemIndex, qubitIndex = indices
            qubit = Qubit.fromStream(self.toAgent.stream, systemIndex, qubitIndex)
        else:
            qubit = None
        # Simulate corruption
        if np.random.rand() > self.attenuation and qubit is not None:
            # Photon was lost due to attenuation effects; collapse state and return nothing
            qubit.measure()
            return None, receiveTime
        else:
            return qubit, receiveTime


