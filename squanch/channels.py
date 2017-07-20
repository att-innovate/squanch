import numpy as np
from Queue import Queue

class QChannel:
    '''
    Base class for a quantum channel
    '''

    def __init__(self, length):
        self.length = length # Physical length of the channel in km
        fiberOpticAttenuation = -0.16  # dB/km, from Yin, et al, Satellite-based entanglement
        # Total attenuation along the fiber, equal to probability of receiving a photon
        decibelLoss = self.length * fiberOpticAttenuation
        self.attenuation = 10 ** (decibelLoss / 10)
        # A queue representing the qubits in transit along the channel
        self.queue = Queue()

    def put(self, qubit):
        # retrievalTime = self.length / lightspeed # When the qubit will arrive at the receiver
        self.queue.put((qubit, None))

    def get(self):
        # Don't give the qubit until the required time
        qubit, receiveTime = self.queue.get()
        # Simulate corruption
        if np.random.rand() > self.attenuation and qubit is not None:
            # Photon was lost due to attenuation effects; collapse state and return nothing
            qubit.measure()
            return None, receiveTime
        else:
            return qubit, receiveTime


