<img src="/docs/source/img/squanchLogo.png" width=400>


## Introduction 

SQUANCH (Simulator for QUAntum Networks and CHannels) is an open-source Python framework for creating performant 
simulations of quantum information processing and transmission. Although it can be used as a general-purpose quantum 
computing simulation library, SQUANCH is designed for simulating quantum networks, acting as a sort of simulated quantum 
playground for you to test ideas for quantum transmission and networking protocols. 

For this purpose, it includes a 
number of extensible and flexible modules that allow you to intuitively design a quantum network, a range of built-in 
quantum error simulations to introduce realism and the need for error corrections in your simulations, and lightweight 
and easily parallelizable systems for manipulating quantum information that allow it to vastly outperform other 
frameworks in certain tasks.

SQUANCH is developed as part of the Intelligent Quantum Networks and Technologies (INQNET) initiative, [a collaboration 
between AT&T and the California Institute of Technology](http://about.att.com/story/beyond_quantum_computing.html).

## Documentation

Documentation for SQUANCH can be found at *LINK HERE*

## Installation 

You can install SQUANCH directly using the Python package manager pip:

```
pip install squanch
```

If you don't have pip, you can get it using `easy_install pip`.

## Examples using SQUANCH

Demonstrations of SQUANCH's capabilities can be found in the demos folder and in the documentation. 
As a simple example, let's consider a simulation of
a transmission of classical data via [quantum superdense coding](https://en.wikipedia.org/wiki/Superdense_coding). In this
scenario, we have three agents, Alice, Bob, and Charlie. Charlie will distribute Bell pairs between Alice and Bob, then Alice will 
send data to Bob by encoding two bits in the Pauli-X and -Z operations for each of her photons. Bob receives Alice's photons and 
disentangles them to reconstruct her information, as shown in the following diagram.

![](docs/source/img/superdenseABC.png)

Simulating complex scenarios with multiple agents like this one is what SQUANCH is designed to do. The quantum states of large
numbers of particles can be efficiently dealt with using `QStream` objects, and the behavior of each agent can be defined by 
extending the built-in `Agent` class. The code necessary to simulate this scenario is given below.

```python
import numpy as np
import matplotlib.image as image
import matplotlib.pyplot as plt
from squanch import *

# Alice sends information to Bob via superdense coding
class Alice(Agent):
    def run(self):
        for _ in self.stream:
            bit1 = self.data.pop(0)
            bit2 = self.data.pop(0)
            q = self.qrecv(charlie)
            if q is not None:
                if bit2 == 1: X(q)
                if bit1 == 1: Z(q)
            self.qsend(bob, q)

# Bob receives Alice's transmissions and reconstructs her information
class Bob(Agent):
    def run(self):
        bits = []
        for _ in self.stream:
            a = self.qrecv(alice)
            c = self.qrecv(charlie)
            if a is not None and c is not None:
                CNOT(a, c)
                H(a)
                bits.extend([a.measure(), c.measure()])
            else:
                bits.extend([0,0])
        self.output(bits)

# Charlie distributes Bell pairs between Alice and Bob
class Charlie(Agent):
    def run(self):
        for qsys in self.stream:
            a, b = qsys.qubits
            H(a)
            CNOT(a, b)
            self.qsend(alice, a)
            self.qsend(bob, b)

# Load an image and serialize it to a bitstream
img = image.imread("img/foundryLogo.bmp")
bits = list(np.unpackbits(img))

# Allocate a shared Hilbert space and output object to pass to agents
mem = Agent.shared_hilbert_space(2, int(len(bits) / 2))
out = Agent.shared_output()

# Make agent instances
alice = Alice(mem, out = out, data = bits)
bob = Bob(mem, out = out)
charlie = Charlie(mem, out = out)

# Connect the agents over simulated fiber optic lines
alice.qconnect(bob, FiberOpticQChannel, length = 1.0)
charlie.qconnect(alice, FiberOpticQChannel, length = 0.5)
charlie.qconnect(bob, FiberOpticQChannel, length = 0.5)

agents = [alice, bob, charlie]
[agent.start() for agent in agents]
[agent.join() for agent in agents]

# Retrieve the transmitted data and reconstruct the original image
received_img = np.reshape(np.packbits(out["Bob"]), img.shape)
plt.imshow(received_img)
``` 

![Alice transmitting an image to Bob over 1km simulated fiber optic cable.](docs/source/img/transmissionDemo.png)