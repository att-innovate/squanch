import numpy as np
import multiprocessing
import channels, qstream


def connectAgents(alice, bob, length = 1.0):
    '''
    Connect Alice and Bob bidirectionally via a simulated fiber optic line

    :param Agent alice: the first Agent
    :param Agent bob: the second Agent
    :param length: the length of the simulated cable
    '''
    # classicalAliceToBob = thing
    # Instantiate quantum channels between Alice and Bob
    quantumAliceToBob = channels.QChannel(length, alice, bob)
    quantumBobToAlice = channels.QChannel(length, bob, alice)
    alice.qChannelsOut[bob] = quantumAliceToBob
    alice.qChannelsIn[bob] = quantumBobToAlice
    bob.qChannelsOut[alice] = quantumBobToAlice
    bob.qChannelsIn[alice] = quantumAliceToBob
    # Make a section of Alice's/Bob's quantum memory for Bob/Alice
    alice.qmem[bob] = []
    bob.qmem[alice] = []


class Agent(multiprocessing.Process):
    '''
    Represents an entity (Alice, Bob, etc.) that can send messages over classical and quantum communication channels.
    Agents have the following properties:

    * Incoming and outgoing classical communciation lines to other agents
    * Incoming and outgoing quantum channels to other agents through which entangled pairs may be distributed
    * Ideal classical memory
    * Quantum memory with some characteristic corruption timescale
    '''

    def __init__(self, name, hilbertSpace, data = None, out = None):
        '''
        :param str name: the unique identifier for the Agent
        :param np.array hilbertSpace: the shared memory pool representing the Hilbert space of the qstream
        :param any data: data to pass to the Agent's process
        :param dict out: shared output dictionary to pass to Agent processes to allow for return-like operations
        '''
        multiprocessing.Process.__init__(self)
        # Name of the agent, e.g. "Alice"
        self.name = name
        self.stream = qstream.QStream.fromArray(hilbertSpace)

        # Agent's clock
        self.time = 0.0
        # self.retardedTime = 0.0
        self.pulseLength = 10 * 10 ** -12  # 10ps photon pulse size

        # Register input data and output structure
        self.data = data
        if out is not None:
            out[self.name] = None
        self.out = out

        # Communication channels are dicts; keys: agent objects, values: channel objects
        self.cChannelsIn = {}
        self.cChannelsOut = {}
        self.qChannelsIn = {}
        self.qChannelsOut = {}

        # Classical memory is a large 1D array
        classicalMemorySize = 2 ** 16
        self.cmem = np.zeros(classicalMemorySize)

        # Quantum memory is an array of "blocks". Each element in a block holds a qubit
        qBlockSize = 256
        numQBlocks = 64
        self.qmem = {}  # ((None,) * qBlockSize,) * numQBlocks
        self.qDecayTimescale = 100.0  # Coherence timescale for qubits in quantum memory

    def __hash__(self):
        '''
        Agents are hashed by their names, which is why they must be unique.
        '''
        return hash(self.name)

    def __eq__(self, other):
        '''
        Agents are compared for equality by their names
        '''
        return self.name == other.name

    def __ne__(self, other):
        return not (self == other)

    @staticmethod
    def generateOutputDict():
        '''
        Generate a shared output dictionary to distribute among agents in separate processes

        :return: an empty multiprocessed Manager.dict()
        '''
        return multiprocessing.Manager().dict()

    def qsend(self, target, qubit):
        '''
        Send a qubit to another agent. The qubit is serialized and passed through a QChannel to the
        targeted agent, which can retrieve the qubit with Agent.qrecv(). ``self.time`` is updated upon
        calling this method.

        :param Agent target: the agent to send the qubit to
        :param Qubit qubit: the qubit to send
        '''
        self.qChannelsOut[target].put(qubit)
        self.time += self.pulseLength

    def csend(self, target, bit):
        pass

    def qrecv(self, origin):
        '''
        Receive a qubit from another connected agent. ``self.time`` is updated upon calling this method.

        :param Agent origin: The agent that previously sent the qubit
        :return: the retrieved qubit, which is also stored in ``self.qmem``
        '''
        qubit, recvTime = self.qChannelsIn[origin].get()
        # Update agent clock
        self.time = max(self.time, recvTime)
        # Add qubit to quantum memory
        self.qmem[origin].append(qubit)
        return qubit

    def crecv(self, origin):
        pass

    def run(self):
        '''This method should be overridden in extended class instances, and cannot take any arguments or
        return any values.'''
        pass

    def output(self, thing):
        '''
        Output something to ``self.out[self.name]``

        :param any thing: the thing to put in the dictionary
        '''
        self.out[self.name] = thing