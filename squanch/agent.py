import multiprocessing
import sys

from squanch import channels
from squanch.qstream import QStream

__all__ = ["Agent"]


class Agent(multiprocessing.Process):
    '''
    Represents an entity (Alice, Bob, etc.) that can send messages over classical and quantum communication channels.
    Agents have the following properties:

    * Incoming and outgoing classical and quantum channels connecting them to other agents
    * Classical memory, implemented simply as a Python dictionary
    * Quantum memory, implemented as a Python dictionary of qubits stored in keys of agent names
    * Runtime logic in the form of an Agent.run() method
    '''

    def __init__(self, qstream, out = None, name = None, data = None):
        '''
        Instantiate an Agent from a unique identifier and a shared memory pool

        :param QStream qstream: the QStream object that the agent operates on
        :param dict out: shared output dictionary to pass to Agent processes to allow for "returns". Default: {}
        :param str name: the unique identifier for the Agent. Default: class name
        :param any data: data to pass to the Agent's process, stored in ``self.data``. Default: None
        '''
        multiprocessing.Process.__init__(self)
        # Name of the agent, e.g. "Alice". Defaults to the name of the class.
        if name is not None:
            self.name = name
        else:
            self.name = self.__class__.__name__

        # Agent's clock
        self.time = 0.0
        # self.retardedTime = 0.0
        self.pulse_length = 10 * 10 ** -12  # 10ps photon pulse size

        # Register input data and output structure
        self.data = data
        if out is None:
            out = {}
        out[self.name] = None
        out[self.name + ":progress"] = 0
        out[self.name + ":progress_max"] = qstream.state.shape[0]
        self.qstream = QStream.from_array(qstream.state, agent = self)
        self.out = out

        # Communication channels are dicts; keys: agent objects, values: channel objects
        self.cchannels_in = {}
        self.cchannels_out = {}
        self.qchannels_in = {}
        self.qchannels_out = {}

        # Classical memory is a large 1D array
        # classicalMemorySize = 2 ** 16
        self.cmem = {}  # np.zeros(classicalMemorySize)

        # Quantum memory is an array of "blocks". Each element in a block holds a qubit
        # qBlockSize = 256
        # numQBlocks = 64
        self.qmem = {}  # ((None,) * qBlockSize,) * numQBlocks
        # self.qDecayTimescale = 100.0  # Coherence timescale for qubits in quantum memory

    def __hash__(self):
        '''
        Agents are hashed by their (unique) names
        '''
        return hash(self.name)

    def __eq__(self, other):
        '''
        Agents are compared for equality by their names.
        '''
        return self.name == other.name

    def __ne__(self, other):
        '''
        Agents are compared for inequality by their names
        '''
        return not (self == other)

    @staticmethod
    def shared_output():
        '''
        Generate a output dictionary stored in a shared memory pool to distribute among agents in separate processes

        :return: an empty multiprocessed Manager.dict()
        '''
        return multiprocessing.Manager().dict()

    def qconnect(self, other, channel = channels.QChannel, **kwargs):
        '''
        Connect Alice and Bob bidirectionally with a specified quantum channel model

        :param Agent other: the other agent to connect to
        :param QChannel channel: the quantum channel model to use
        :param \**kwargs: optional channel arguments
        '''
        # Instantiate quantum channels between Alice and Bob
        qchannel_alice_to_bob = channel(self, other, **kwargs)
        qchannel_bob_to_alice = channel(other, self, **kwargs)
        self.qchannels_out[other] = qchannel_alice_to_bob
        self.qchannels_in[other] = qchannel_bob_to_alice
        other.qchannels_out[self] = qchannel_bob_to_alice
        other.qchannels_in[self] = qchannel_alice_to_bob
        # Make a section of Alice's/Bob's quantum memory for Bob/Alice
        self.qmem[other] = []
        other.qmem[self] = []

    def qsend(self, target, qubit):
        '''
        Send a qubit to another agent. The qubit is serialized and passed through a QChannel to the
        targeted agent, which can retrieve the qubit with Agent.qrecv(). ``self.time`` is updated upon
        calling this method.

        :param Agent target: the agent to send the qubit to
        :param Qubit qubit: the qubit to send
        '''
        self.qchannels_out[target].put(qubit)
        self.time += self.pulse_length

    def qrecv(self, origin):
        '''
        Receive a qubit from another connected agent. ``self.time`` is updated upon calling this method.

        :param Agent origin: The agent that previously sent the qubit
        :return: the retrieved qubit, which is also stored in ``self.qmem``
        '''
        qubit, recvTime = self.qchannels_in[origin].get()
        # Update agent clock
        self.time = max(self.time, recvTime)
        # Add qubit to quantum memory
        self.qmem[origin].append(qubit)
        return qubit

    def qstore(self, qubit):
        '''
        Store a qubit in quantum memory. Equivalent to ``self.qmem[self].append(qubit)``.

        :param Qubit qubit: the qubit to store
        '''
        self.qmem[self].append(qubit)

    def cconnect(self, other, channel = channels.CChannel, **kwargs):
        '''
        Connect Alice and Bob bidirectionally with a specified classical channel model

        :param Agent other: the other agent to connect to
        :param CChannel channel: the classical channel model to use
        :param \**kwargs: optional channel arguments
        '''
        # Instantiate classical channels between Alice and Bob
        cchannel_alice_to_bob = channel(self, other, **kwargs)
        cchannel_bob_to_alice = channel(other, self, **kwargs)
        self.cchannels_out[other] = cchannel_alice_to_bob
        self.cchannels_in[other] = cchannel_bob_to_alice
        other.cchannels_out[self] = cchannel_bob_to_alice
        other.cchannels_in[self] = cchannel_alice_to_bob
        # Make a section of Alice's/Bob's classical memory for Bob/Alice
        self.cmem[other] = []
        other.cmem[self] = []

    def csend(self, target, thing):
        '''
        Send a serializable object to another agent. The transmission time is updated by (number of bits) pulse lengths.

        :param Agent target: the agent to send the transmission to
        :param any thing: the object to send
        '''

        self.cchannels_out[target].put(thing)
        self.time += sys.getsizeof(thing) * 8 * self.pulse_length

    def crecv(self, origin):
        '''
        Receive a serializable object from another connected agent. ``self.time`` is updated upon calling this method.

        :param Agent origin: The agent that previously sent the qubit
        :return: the retrieved object, which is also stored in ``self.cmem``
        '''
        thing, recvTime = self.cchannels_in[origin].get()
        # Update agent clock
        self.time = max(self.time, recvTime)
        # Add qubit to quantum memory
        self.cmem[origin].append(thing)
        return thing

    def run(self):
        '''Runtime logic for the Agent; this method should be overridden in child classes.'''
        pass

    def output(self, thing):
        '''
        Output something to ``self.out[self.name]``

        :param any thing: the thing to put in the dictionary
        '''
        self.out[self.name] = thing

    def update_progress(self, value):
        '''
        Update the progress of this agent in the shared output dictionary. Used in Simulation.progress_monitor().

        :param value: the value to update the progress to (out of a max of len(self.qstream))
        '''
        self.out[self.name + ":progress"] = value

    def increment_progress(self):
        '''
        Adds 1 to the current progress
        '''
        self.out[self.name + ":progress"] += 1
