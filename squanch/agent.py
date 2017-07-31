import numpy as np
import channels


def connectAgents(alice, bob, length = 1.0):
    # classicalAliceToBob = thing
    # Instantiate quantum channels between Alice and Bob
    quantumAliceToBob = channels.QChannel(length)
    quantumBobToAlice = channels.QChannel(length)
    alice.qChannelsOut[bob] = quantumAliceToBob
    alice.qChannelsIn[bob] = quantumBobToAlice
    bob.qChannelsOut[alice] = quantumBobToAlice
    bob.qChannelsIn[alice] = quantumAliceToBob
    # Make a section of Alice's/Bob's quantum memory for Bob/Alice
    alice.qmem[bob] = []
    bob.qmem[alice] = []


class Agent:
    '''
    Represents an entity (Alice, Bob, etc.) that can send messages over classical and quantum communication channels.
    Agents have the following properties:
    - Incoming and outgoing classical communciation lines to other agents
    - Incoming and outgoing quantum channels to other agents through which entangled pairs may be distributed
    - Ideal classical memory
    - Quantum memory with some characteristic corruption timescale
    '''

    def __init__(self, name):
        # Name of the agent, e.g. "Alice"
        self.name = name

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

    def qsend(self, target, qubit):
        self.qChannelsOut[target].put(qubit)

    def csend(self, target, bit):
        pass

    def qrecv(self, origin):
        qubit, recvTime = self.qChannelsIn[origin].get()
        self.qmem[origin].append(qubit)

    def crecv(self, origin):
        pass
