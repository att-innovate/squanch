import numpy as np
import multiprocessing
import channels, qstream


def connectAgents(alice, bob, length = 1.0):
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
    - Incoming and outgoing classical communciation lines to other agents
    - Incoming and outgoing quantum channels to other agents through which entangled pairs may be distributed
    - Ideal classical memory
    - Quantum memory with some characteristic corruption timescale
    '''

    def __init__(self, name, hilbertSpace, outDict = None):
        multiprocessing.Process.__init__(self)
        # Name of the agent, e.g. "Alice"
        self.name = name
        self.stream = qstream.QStream.fromArray(hilbertSpace)
        if outDict is not None:
            outDict[self.name] = None
        self.outDict = outDict

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
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not (self == other)

    @staticmethod
    def generateOutputDict():
        return multiprocessing.Manager().dict()

    def qsend(self, target, qubit):
        self.qChannelsOut[target].put(qubit)

    def csend(self, target, bit):
        pass

    def qrecv(self, origin):
        qubit, recvTime = self.qChannelsIn[origin].get()
        self.qmem[origin].append(qubit)
        return qubit

    def crecv(self, origin):
        pass

    def run(self):
        '''This method should be overridden in extended class instances'''
        pass

    def output(self, thing):
        self.outDict[self.name] = thing