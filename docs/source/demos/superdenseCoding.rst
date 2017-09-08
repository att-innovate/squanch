.. _superdenseCodingDemo:

Superdense Coding
=================

Superdense coding is a process whereby two parties sharing an entangled pair can send two classical bits with a single qubit. Conecptually, it is the inverse of :ref:`quantum teleportation <teleportationDemo>`.

Protocol
--------

.. image:: https://upload.wikimedia.org/wikipedia/commons/b/b7/Superdense_coding.png

We'll be using the above circuit diagram to describe a three-party quantum superdense coding protocol. There are three agents: Charlie distributes entangled particles to Alice and Bob, Alice encodes her information in her particles and sends them to Bob, who decodes the information by matching Alice's qubits with his own qubits received from Charlie.

	1. Charlie generates EPR pairs in the state :math:`\frac{1}{\sqrt{2}} \left (\lvert 00 \rangle + \lvert 11 \rangle \right )`. He sends one particle to Alice and the other to Bob.

	2. Alice encodes her two bits of classical inforation in the relative sign and phase of her qubit by acting with the Pauli-X and -Z gates. Formally, if she has two bits, :math:`b_1 and b_2`, she applies X if :math:`b_2 = 1` and then applies Z if :math:`b_1 = 1`. She then sends the modified qubit to Bob.

	3. Bob disentangles the X and Z components of the qubit by applying CNOT and H to Alice's qubit and Charlie's qubit. He then measures each of Alice's and Charlie's qubits to obtain :math:`b_1` and :math:`b_2`, respectively.

Implementation
--------------

Because superdense coding transmits classical information, it makes for a good protocol to visually demonstrate both the tranmission of the information and some of SQUANCH's simulated errors. (This also makes it a good demonstration for implementing classical and quantum error corrections, although we won't do that in this demo.) The protocol we'll be implementing looks like this at a conceptual level:

.. image:: ../img/superdenseABC.png

First, let's import the modules we'll need.

.. code:: python

	import numpy as np
	import time 
	import matplotlib.image as image
	import matplotlib.pyplot as plt
	from squanch.agent import *
	from squanch.gates import *
	from squanch.qstream import *

Now, as usual, we'll want to define child `Agent` classes that implement the behavior we want. For Charlie, we'll want to include the behavior to make an EPR pair and distribute it to Alice and Bob.

.. code:: python

	class Charlie(Agent):
	    '''Charlie distributes Bell pairs between Alice and Bob.'''
	    def run(self):
	        for qSys in self.stream:
	            a, b = qSys.qubits
	            H(a)
	            CNOT(a, b)
	            self.qsend(alice, a)
	            self.qsend(bob, b)

For Alice, we'll want to include the transmission behavior. We'll pass in the data that she wants to transmit as a 1D array in an input argument when we instantiate her, and it will be stored in `self.data`. 

.. code:: python

	class Alice(Agent):
	    '''Alice sends information to Bob via superdense coding'''
	    def run(self):
	        for i in range(len(self.stream)):
	            bit1, bit2 = self.data[2 * i], self.data[2 * i + 1]
	            q = self.qrecv(charlie)
	            if q is not None:
	                if bit2 == 1: X(q)
	                if bit1 == 1: Z(q)
	            self.qsend(bob, q)

Finally, for Bob, we'll want to include the disentangling and measurement behavior, and we'll want to output his measured data using `self.output`, which passes it to the parent process through the `sharedOutputDict` that is provided to agents on instantiation.

.. code:: python

	class Bob(Agent):
	    '''Bob receives Alice's transmissions and reconstructs her information'''
	    def run(self):
	        self.data = np.zeros(2 * len(self.stream), dtype = np.uint8)
	        for i in range(len(self.stream)):
	            a = self.qrecv(alice)
	            c = self.qrecv(charlie)
	            if a is not None and c is not None:
	                CNOT(a, c)
	                H(a)
	                self.data[2 * i] = a.measure()
	                self.data[2 * i + 1] = c.measure()
	        self.output(self.data)

Now, we want to instantiate Alice, Bob, and Charlie, and run the protocol. To do this, we'll need to pass in the data that Alice will send to Bob (which will be an image serialized to a 1D array of bits), and we'll also need to provide the agents with appropriate arguments for the Hilbert space they will share as well as an output structure to push their data to. (This is necessary because all agents run in separate processes, so explicitly shared memory structures must be passed to them.)

.. code:: python 

	# Load an image and serialize it to a bitstream
	imgArray = image.imread("img/foundryLogo.bmp")
	imgBitstream = np.unpackbits(imgArray)

	# Allocate a shared Hilbert space and output object to pass to agents
	mem = sharedHilbertSpace(2, len(imgBitstream) / 2)
	out = sharedOutputDict()

	# Make agent instances
	alice = Alice(mem, data = imgBitstream)
	bob = Bob(mem, out = out)
	charlie = Charlie(mem)

Let's connect the agents with some simulated length parameter (for time simulation purposes and for application of errors). Let's say that Alice and Bob are separated by a 1km fiber optic cable, and Charlie is at the midpoint, 0.5km away from each. Once we've connected the agents, we just need to run all of the agent processes with `start()` and wait for them to finish with `join()`.

.. code:: python 

	# Connect the agents over simulated fiber optic lines
	connectAgents(alice, bob, length = 1.0)
	connectAgents(alice, charlie, length = 0.5)
	connectAgents(bob, charlie, length = 0.5)
	
	# Run the agents
	start = time.time()
	agents = [alice, bob, charlie]
	[agent.start() for agent in agents]
	[agent.join() for agent in agents] 
	print "Transmitted {} bits in {:.3f}s.".format(len(out["Bob"]), time.time() - start)

Finally, let's retrieve Bob's data and repackage it into an image array, then compare the results.

.. code:: python

	receivedArray = np.reshape(np.packbits(out["Bob"]), imgArray.shape)
	f, ax = plt.subplots(1, 2, figsize = (8, 4))
	ax[0].imshow(imgArray)
	ax[0].axis('off')
	ax[0].title.set_text("Alice's image")
	ax[1].imshow(receivedArray)
	ax[1].axis('off')
	ax[1].title.set_text("Bob's image")
	plt.tight_layout()
	plt.show()

.. image:: ../img/transmissionDemo.png 

Source code
-----------

The full source code for this demonstration is available in the demos directory of the SQUANCH repository.
