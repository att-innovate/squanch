# Import everything
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mp
from matplotlib import image
# PyQuil stuff
import pyquil.quil as pq  # Quil language
import pyquil.api as api  # Rigetti forest api
from pyquil.gates import *  # All QC logical gates
# SQUANCH stuff
from squanch.agent import *
# from squanch.gates import *
import squanch.gates as g
from squanch.qstream import *
# Quintuple
from QuantumComputer import *

imgData = image.imread("img/attLogo.bmp")
fiberOpticAttenuation = -0.16  # dB/km, from Yin, et al, Satellite-based entanglement
cableLength = 1  # km, let's just call it this for now
# Total attenuation along the fiber, equal to probability of receiving a photon
decibelLoss = cableLength * fiberOpticAttenuation
cableAttenuation = 10 ** (decibelLoss / 10)


# SQUANCH performance test without Agents ==============================================================================
print "Running SQUANCH performance test with no agents..."

# Load an image and serialize it to a bitstream
imgBitstream = np.unpackbits(imgData)
outData = np.zeros(len(imgBitstream), dtype = np.uint8)
stream = QStream(2, len(imgBitstream)/2)
start = time.time()
for i, qSys in enumerate(stream):
    a, b = qSys.qubits
    g.H(a)
    g.CNOT(a, b)
    bit1, bit2 = imgBitstream[2 * i], imgBitstream[2 * i + 1]
    if bit2 == 1: g.X(a)
    if bit1 == 1: g.Z(a)
    if np.random.rand() > cableAttenuation:
        continue
    if np.random.rand() > cableAttenuation:
        continue
    g.CNOT(a, b)
    g.H(a)
    outData[2 * i] = a.measure()
    outData[2 * i + 1] = b.measure()

print "Transmitted {} bits in {:.3f}s.".format(len(outData), time.time() - start)

receivedArray = np.reshape(np.packbits(outData), imgData.shape)
f, ax = plt.subplots(1, 2, figsize = (8, 4))
ax[0].imshow(imgData)
ax[0].axis('off')
ax[0].title.set_text("Alice's image")
ax[1].imshow(receivedArray)
ax[1].axis('off')
ax[1].title.set_text("Bob's image")
plt.tight_layout()
plt.show()

# SQUANCH performance test =============================================================================================

print "Running SQUANCH performance test..."


class Alice(Agent):
    '''Alice sends information to Bob via superdense coding'''

    def run(self):
        for i, qSys in enumerate(self.stream):
            a, b = qSys.qubits
            g.H(a)
            g.CNOT(a, b)
            self.qsend(bob, b)
            bit1, bit2 = self.data[2 * i], self.data[2 * i + 1]
            if bit2 == 1: g.X(a)
            if bit1 == 1: g.Z(a)
            self.qsend(bob, a)


class Bob(Agent):
    '''Bob receives Alice's transmissions and reconstructs her information'''

    def run(self):
        self.data = np.zeros(2 * self.stream.numSystems, dtype = np.uint8)
        for i in range(self.stream.numSystems):
            b = self.qrecv(alice)
            a = self.qrecv(alice)
            if a is not None and b is not None:
                g.CNOT(a, b)
                g.H(a)
                self.data[2 * i] = a.measure()
                self.data[2 * i + 1] = b.measure()
        self.output(self.data)


# Allocate a shared Hilbert space and output object to pass to agents
mem = sharedHilbertSpace(2, len(imgBitstream) / 2)
out = sharedOutputDict()

# Make agent instances
alice = Alice("Alice", mem, data = imgBitstream)
bob = Bob("Bob", mem, out = out)
# Connect the agents over simulated fiber optic lines
connectAgents(alice, bob, length = 1.0)
# Run the agents
start = time.time()
agents = [alice, bob]
[agent.start() for agent in agents]
[agent.join() for agent in agents]
print "Transmitted {} bits in {:.3f}s.".format(len(out["Bob"]), time.time() - start)

receivedArray = np.reshape(np.packbits(out["Bob"]), imgData.shape)
f, ax = plt.subplots(1, 2, figsize = (8, 4))
ax[0].imshow(imgData)
ax[0].axis('off')
ax[0].title.set_text("Alice's image")
ax[1].imshow(receivedArray)
ax[1].axis('off')
ax[1].title.set_text("Bob's image")
plt.tight_layout()
plt.show()

# Quintuple performance test ===========================================================================================

print "Running Quintuple performance test..."

start = time.time()

quintupleBits = np.zeros(len(imgBitstream), dtype = np.uint8)


def quintupleTransmitBits(bit1, bit2):
    qc = QuantumComputer()
    # Prepare a bell state
    qc.apply_gate(Gate.X, "q1")
    qc.apply_two_qubit_gate_CNOT("q1", "q2")
    # Encode data
    if bit2 == 1:
        qc.apply_gate(Gate.X, "q1")
    if bit1 == 1:
        qc.apply_gate(Gate.Z, "q1")
    qc.apply_two_qubit_gate_CNOT("q1", "q2")
    qc.apply_gate(Gate.H, "q1")
    qc.measure("q1")
    qc.measure("q2")

    if np.array_equal(qc.qubits.get_quantum_register_containing("q1").get_state(), np.matrix([[0], [1]])):
        b1 = 1
    else:
        b1 = 0
    if np.array_equal(qc.qubits.get_quantum_register_containing("q2").get_state(), np.matrix([[0], [1]])):
        b2 = 1
    else:
        b2 = 0

    return b1, b2


for i in range(0, len(imgBitstream), 2):
    b1, b2 = quintupleTransmitBits(imgBitstream[i], imgBitstream[i + 1])
    if np.random.rand() > cableAttenuation:
        b1, b2 = 0, 0
    if np.random.rand() > cableAttenuation:
        b1, b2 = 0, 0
    quintupleBits[i] = b1
    quintupleBits[i + 1] = b2

print "Transmitted {} bits in {:.3f}s.".format(len(out["Bob"]), time.time() - start)

receivedArray = np.reshape(np.packbits(quintupleBits), imgData.shape)
f, ax = plt.subplots(1, 2, figsize = (8, 4))
ax[0].imshow(imgData)
ax[0].axis('off')
ax[0].title.set_text("Alice's image")
ax[1].imshow(receivedArray)
ax[1].axis('off')
ax[1].title.set_text("Bob's image")
plt.tight_layout()
plt.show()

# PyQuil performance test ==============================================================================================

print "Running PyQuil performance test..."


def quilAttenuatedSuperdenseTransmission(bit1, bit2):
    alice = 0
    bob = 1

    # Alice prepares a bell pair
    Hilbert = pq.Program(H(alice), CNOT(alice, bob))

    if bit2 == 1:
        Hilbert.inst(X(alice))
    if bit1 == 1:
        Hilbert.inst(Z(alice))

    Hilbert.inst(CNOT(alice, bob),
                 H(alice))

    # Measure the results
    Hilbert.measure(alice, alice)
    Hilbert.measure(bob, bob)

    return Hilbert


def quilAttenuatedIntTransmission(value, qvm):
    '''Transmit an 8-bit unsigned integer value including attenuation effects'''
    bits = np.unpackbits(np.array([value], dtype = np.uint8))
    receivedBits = np.zeros(8, dtype = np.uint8)

    for i in range(4):
        b1, b2 = qvm.run(quilAttenuatedSuperdenseTransmission(bits[2 * i], bits[2 * i + 1]), [0, 1])[0]
        if np.random.rand() > cableAttenuation:
            b1, b2 = 0, 0
        if np.random.rand() > cableAttenuation:
            b1, b2 = 0, 0
        receivedBits[2 * i] = b1
        receivedBits[2 * i + 1] = b2

    return np.packbits(receivedBits)[0]


def quilAttenuatedArrayTransmission(array, qvm):
    receivedArray = np.zeros(array.shape, dtype = np.uint8)
    iterator = np.nditer(array, flags = ['multi_index'])

    while not iterator.finished:
        if iterator.iterindex % 100 == 0:
            print "Iteration {}/{}".format(iterator.iterindex, iterator.itersize)
        receivedElement = quilAttenuatedIntTransmission(iterator[0], qvm)
        receivedArray[iterator.multi_index] = receivedElement
        iterator.iternext()
    return receivedArray


print "Original image:"
plt.imshow(imgData)

qvm = api.SyncConnection()

# Transmit the image with the attenuated superdense protocol
start = time.time()
receivedArray = quilAttenuatedArrayTransmission(imgData, qvm)
stop = time.time()
print "Reconstructed transmitted image accounting " \
      "for attenuation effects: (elapsed time: {} sec)".format(stop - start)
plt.imshow(receivedArray)

transmissionRate = receivedArray.nbytes / (stop - start)
print "Transmission rate: {}B/s".format(transmissionRate)
