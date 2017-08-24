# SQUANCH
### Simulator for QUAntum Networks and CHannels


## Introduction 

SQUANCH is a Python-based framework for creating performant simulations of distributed quantum information processing and transmission over networks.
It is computationally optimized for dealing with a large number of disjoint entangled quantum systems, such as simulating 
millions Bell pairs for the purpose of information transfer.

SQUANCH includes a number of built-in error simulations to characterize classical and quantum errors associated with transferring
qubits over quantum channels, such as spontaneous attenuation losses, dephasing and depolarizing errors, and decoherence. 
Error models can easily be changed or added, allowing researchers to test ideas for error-resistant quantum communication processes.

## Documentation

Documentation for SQUANCH can be found at *LINK HERE*

## Installation 

You can *EVENTUALLY* install SQUANCH with `pip` using:

`pip install squanch`

## Examples

Demonstrations of SQUANCH's capabilities can be found in the demos folder. As a simple example, let's consider a simulation of
a transmission of classical data via [quantum superdense coding](https://en.wikipedia.org/wiki/Superdense_coding). In this
scenario, we have three agents, Alice, Bob, and Charlie. Charlie will distribute Bell pairs between Alice and Bob, then Alice will 
send data to Bob by encoding two bits in the Pauli-X and -Z operations for each of her photons. Bob receives Alice's photons and 
disentangles them to reconstruct her information, as shown in the following diagram.

![](img/superdenseABC.png)

Simulating complex scenarios with multiple agents like this one is what SQUANCH is designed to do. The quantum states of large
numbers of particles can be efficiently dealt with using `QStream` objects, and the behavior of each agent can be defined by 
extending the built-in `Agent` class. The code necessary to simulate this scenario is given below.

```python
import numpy as np
import matplotlib.image as image
import matplotlib.pyplot as plt
from squanch.agent import *
from squanch.gates import *
from squanch.qstream import *

# Alice sends information to Bob via superdense coding
class Alice(Agent):
    def run(self):
        for i in range(self.stream.numSystems):
            bit1, bit2 = self.data[2 * i], self.data[2 * i + 1]
            q = self.qrecv(charlie)
            if q is not None:
                if bit2 == 1: X(q)
                if bit1 == 1: Z(q)
            self.qsend(bob, q)

# Bob receives Alice's transmissions and reconstructs her information
class Bob(Agent):
    def run(self):
        self.data = np.zeros(2 * self.stream.numSystems, dtype = np.uint8)
        for i in range(self.stream.numSystems):
            a = self.qrecv(alice)
            c = self.qrecv(charlie)
            if a is not None and c is not None:
                CNOT(a, c)
                H(a)
                self.data[2 * i] = a.measure()
                self.data[2 * i + 1] = c.measure()
        self.output(self.data)

# Charlie distributes Bell pairs between Alice and Bob
class Charlie(Agent):
    def run(self):
        for i in range(self.stream.numSystems):
            a, b = self.stream.head().qubits
            H(a)
            CNOT(a, b)
            self.qsend(alice, a)
            self.qsend(bob, b)

# Load an image and serialize it to a bitstream
imgArray = image.imread("img/foundryLogo.bmp")
imgBitstream = np.unpackbits(imgArray)

# Allocate a shared Hilbert space and output object to pass to agents
mem = sharedHilbertSpace(2, len(imgBitstream) / 2)
out = sharedOutputDict()

# Make agent instances, connect via simulated fiber optic lines, and run them
alice = Alice("Alice", mem, data = imgBitstream)
bob = Bob("Bob", mem, out = out)
charlie = Charlie("Charlie", mem)
connectAgents(alice, bob, length = 1.0)
connectAgents(alice, charlie, length = 0.5)
connectAgents(bob, charlie, length = 0.5)
agents = [alice, bob, charlie]
[agent.start() for agent in agents]
[agent.join() for agent in agents]

# Retrieve the transmitted data and reconstruct the original image
receivedImg = np.reshape(np.packbits(out["Bob"]), imgArray.shape)
plt.imshow(receivedImg)
plt.show()
``` 

![Alice transmitting an image to Bob over 1km simulated fiber optic cable.](img/transmissionDemo.png)