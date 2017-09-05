import sys
import numpy as np
import multiprocessing
from multiprocessing import sharedctypes
import ctypes
import channels, qstream


# Shared memory structures

def sharedOutputDict():
    '''
    Generate a shared output dictionary to distribute among agents in separate processes

    :return: an empty multiprocessed Manager.dict()
    '''
    return multiprocessing.Manager().dict()


def sharedHilbertSpace(systemSize, numSystems):
    '''
    Allocate a portion of shareable c-type memory to create a numpy array that is sharable between processes

    :param int systemSize: number of entangled qubits in each quantum system; each system has dimension 2^systemSize
    :param int numSystems: number of small quantum systems in the data stream
    :return: a blank, sharable, numSystems x 2^systemSize x 2^systemSize array of np.complex64 values
    '''
    dim = 2 ** systemSize
    mallocMem = sharedctypes.RawArray(ctypes.c_double, numSystems * dim * dim)
    array = np.frombuffer(mallocMem, dtype = np.complex64).reshape((numSystems, dim, dim))
    qstream.QStream.reformatArray(array)
    return array


# Connect agents

def connectAgents(alice, bob, length = 0.0):
    '''
    Connect Alice and Bob bidirectionally via a simulated fiber optic line

    :param Agent alice: the first Agent
    :param Agent bob: the second Agent
    :param float length: the length of the simulated cable in km; default value: 0.0km
    '''
    # classicalAliceToBob = thing
    # Instantiate quantum channels between Alice and Bob
    # quantumAliceToBob = channels.QChannel(alice, bob, length)
    # quantumBobToAlice = channels.QChannel(bob, alice, length)
    quantumAliceToBob = channels.FiberOpticQChannel(alice, bob, length)
    quantumBobToAlice = channels.FiberOpticQChannel(bob, alice, length)
    alice.qChannelsOut[bob] = quantumAliceToBob
    alice.qChannelsIn[bob] = quantumBobToAlice
    bob.qChannelsOut[alice] = quantumBobToAlice
    bob.qChannelsIn[alice] = quantumAliceToBob
    # Instantiate classical channels between Alice and Bob
    classicalAliceToBob = channels.CChannel(alice, bob, length)
    classicalBobToAlice = channels.CChannel(bob, alice, length)
    alice.cChannelsOut[bob] = classicalAliceToBob
    alice.cChannelsIn[bob] = classicalBobToAlice
    bob.cChannelsOut[alice] = classicalBobToAlice
    bob.cChannelsIn[alice] = classicalAliceToBob
    # Make a section of Alice's/Bob's quantum memory for Bob/Alice
    alice.qmem[bob] = []
    bob.qmem[alice] = []
    # Make a section of Alice's/Bob's classical memory for Bob/Alice
    alice.cmem[bob] = []
    bob.cmem[alice] = []


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
        Instantiate an Agent from a unique identifier and a shared memory pool

        :param str name: the unique identifier for the Agent
        :param np.array hilbertSpace: the shared memory pool representing the Hilbert space of the qstream
        :param any data: data to pass to the Agent's process, stored in ``self.data``
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
        self.cmem = {}  # np.zeros(classicalMemorySize)

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
        Agents are compared for equality by their names.
        '''
        return self.name == other.name

    def __ne__(self, other):
        '''
        Overridden inequality operator, for good practice.
        '''
        return not (self == other)

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

    def csend(self, target, thing):
        '''
        Send a serializable object to another agent. The transmission time is updated by (number of bits) pulse lengths.

        :param Agent target: the agent to send the transmission to
        :param any thing: the object to send
        '''

        self.cChannelsOut[target].put(thing)
        self.time += sys.getsizeof(thing) * 8 * self.pulseLength

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

    def qstore(self, qubit):
        '''
        Store a qubit in quantum memory. Equivalent to ``self.qmem[self].append(qubit)``.

        :param Qubit qubit: the qubit to store
        '''
        self.qmem[self].append(qubit)

    def crecv(self, origin):
        '''
        Receive a serializable object from another connected agent. ``self.time`` is updated upon calling this method.

        :param Agent origin: The agent that previously sent the qubit
        :return: the retrieved object, which is also stored in ``self.cmem``
        '''
        thing, recvTime = self.cChannelsIn[origin].get()
        # Update agent clock
        self.time = max(self.time, recvTime)
        # Add qubit to quantum memory
        self.cmem[origin].append(thing)
        return thing

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
