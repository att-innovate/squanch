import multiprocessing
import sys

from squanch import errors
from squanch.qubit import Qubit

__all__ = ["QChannel", "CChannel", "FiberOpticQChannel"]


class QChannel:
    '''
    Base class for a quantum channel connecting two agents
    '''

    def __init__(self, from_agent, to_agent, length = 0.0, errors = ()):
        '''
        Instantiate the quantum channel

        :param Agent from_agent: sending agent
        :param Agent to_agent: receiving agent
        :param float length: length of quantum channel in km; default: 0.0km
        :param QError[] errors: list of error models to apply to qubits in this channel; default: [] (no errors)
        '''
        # Register agent connections
        self.from_agent = from_agent
        self.to_agent = to_agent

        # Signal propagation properties
        self.length = length  # Physical length of the channel in km
        self.signal_speed = 2.998 * 10 ** 5  # Speed of light in km/s

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
        time_of_arrival = self.from_agent.time + self.from_agent.pulse_length + (self.length / self.signal_speed)
        if qubit is not None:
            self.queue.put((qubit.serialize(), time_of_arrival))
        else:
            self.queue.put((None, time_of_arrival))

    def get(self):
        '''
        Retrieve a qubit by reference from the channel queue, applying errors upon retrieval

        :return: tuple: (the qubit with errors applied (possibly ``None``), receival time)
        '''
        indices, receive_time = self.queue.get()
        if indices is not None:
            system_index, qubit_index = indices
            qubit = Qubit.from_stream(self.to_agent.qstream, system_index, qubit_index)
        else:
            qubit = None

        # Apply errors
        for error in self.errors:
            qubit = error.apply(qubit)

        # Return modified qubit and return time
        return qubit, receive_time


class CChannel:
    '''
    Base class for a classical channel connecting two agents
    '''

    def __init__(self, from_agent, to_agent, length = 0.0):
        '''
        Instantiate the quantum channel

        :param Agent from_agent: sending agent
        :param Agent to_agent: receiving agent
        :param float length: length of fiber optic line in km; default: 0.0km
        '''
        # Register agent connections
        self.from_agent = from_agent
        self.to_agent = to_agent

        # Signal propagation
        self.length = length  # Physical length of the channel in km
        self.signal_speed = 2.998 * 10 ** 5  # Speed of light in km/s

        # The channel queue
        self.queue = multiprocessing.Queue()

    def put(self, thing):
        '''
        Serialize and push a serializable object into the channel queue

        :param any thing: the qubit to send
        '''
        # Calculate the time of arrival
        pulse_time = sys.getsizeof(thing) * 8 * self.from_agent.pulse_length
        time_of_arrival = self.from_agent.time + pulse_time + (self.length / self.signal_speed)
        self.queue.put((thing, time_of_arrival))

    def get(self):
        '''
        Retrieve a classical object form the queue

        :return: tuple: (the object, receival time)
        '''
        thing, receive_time = self.queue.get()
        return thing, receive_time


class FiberOpticQChannel(QChannel):
    '''
    Represents a fiber optic line with attenuation errors
    '''

    def __init__(self, from_agent, to_agent, length = 0.0):
        '''
        Instantiate the simulated fiber optic quantum channel

        :param Agent from_agent: sending agent
        :param Agent to_agent: receiving agent
        :param float length: length of fiber optic channel in km; default: 0.0km
        '''
        QChannel.__init__(self, from_agent, to_agent, length = length)

        # Register attenuation errors
        self.errors = [
            errors.AttenuationError(self),
            # errors.RandomUnitaryError(self, 2*np.pi / 100),
            # errors.SystematicUnitaryError(self, 2*np.pi / 10),
        ]
