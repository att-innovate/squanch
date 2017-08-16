import numpy as np
import multiprocessing
from qubit import Qubit

class QChannel:
    '''
    Base class for a quantum channel
    '''

    def __init__(self, length, fromAgent, toAgent):
        self.length = length # Physical length of the channel in km
        self.fromAgent = fromAgent
        self.toAgent = toAgent
        fiberOpticAttenuation = -0.16  # dB/km, from Yin, et al, Satellite-based entanglement
        # Total attenuation along the fiber, equal to probability of receiving a photon
        decibelLoss = self.length * fiberOpticAttenuation
        self.attenuation = 10 ** (decibelLoss / 10)
        # A queue representing the qubits in transit along the channel
        self.queue = multiprocessing.Queue()

    def put(self, qubit):
        # retrievalTime = self.length / lightspeed # When the qubit will arrive at the receiver
        if qubit is not None:
            self.queue.put((qubit.serialize(), None))
        else:
            self.queue.put((None, None))

    def get(self):
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


