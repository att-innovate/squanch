Getting Started
===============

Requirements
------------

SQUANCH is programmed in Python 2.7 and NumPy. You can obtain both of these, along with a host of other scientific computing tools, from the `Anaconda <https://www.continuum.io/downloads>`__ package.

Installation
------------

You can install SQUANCH directly using the Python package manager pip:

.. code:: python

	pip install pyquil

If you don't have pip, you can get it using ``easy_install pip``.

The basics of SQUANCH
---------------------

Before we can run our first simulation, we'll need to introduce the notions of a ``QSystem`` and ``Qubit``. A ``QSystem`` is the fundamental unit of information in SQUANCH, and maintains the quantum state of a multi-particle, maximally-entangleable system. A ``QSystem`` also contains references to the ``Qubit`` s that comprise it, which allows you to work with them in a more intuitive manner. To manipulate qubits and quantum systems, we use quantum gates. Let's play around with these concepts for a moment.

.. code:: python

	from squanch.qubit import *
	from squanch.gates import *

	# Prepare a two-qubit system, which defaults to the |00> state
	qSys = QSystem(2) 

The state of a quantum system is tracked as a complex-valued density matrix in the computational basis:

.. code:: python 
	
	qSys.state 

.. parsed-literal::

	array([[ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	       [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	       [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	       [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j]], dtype=complex64)

``QSystem`` s also have a generator to yield their consistuent qubits. Note that this isn't the same as a list, as the qubits are instantiated only when they are asked for, not on instantiation of the QSystem. (This saves on overhead, especially in cases when only one qubit in a system of many needs to be modified.) 

.. code:: python
	
	qSys.qubits

.. parsed-literal:: 

	<generator object <genexpr> at 0x107000460>

You can access and work with the qubits of a system either by pattern matching them:

.. code:: python
	
	a, _ = qSys.qubits
	print a

.. parsed-literal::

	<squanch.qubit.Qubit instance at 0x10d540ea8>

or by requesting a specific qubit directly:

.. code:: python 

	a2 = qSys.qubit(0)
	print a

.. parsed-literal::

	<squanch.qubit.Qubit instance at 0x10d533878> 

Even though ``a`` and ``a2`` are separate objects in memory, they both represent the same qubit and will manipulate the same parent ``QSystem``, which can be referenced using ``a.qSystem``:

.. code:: python 

	a.qSystem
	<squanch.qubit.QSystem instance at 0x107cfc3b0>

	a2.qSystem
	<squanch.qubit.QSystem instance at 0x107cfc3b0>

For example, applying a Hadamard transformation to each of them yields the expected results:

.. code:: python

	H(a)
	qSys.state

.. parsed-literal::

	array([[ 0.5+0.j,  0.0+0.j,  0.5+0.j,  0.0+0.j],
	       [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	       [ 0.5+0.j,  0.0+0.j,  0.5+0.j,  0.0+0.j],
	       [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j]], dtype=complex64)

And applying the same (self-adjoint) transformation to ``a2`` gives the original :math:`\lvert 00 \rangle` state (ignoring machine errors):

.. code:: python 

	H(a2)
	qSys.state

.. parsed-literal::

	array([[  1.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j],
	       [  0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j],
	       [ -2.23711427e-17+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j],
	       [  0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j,   0.00000000e+00+0.j]], dtype=complex64)


Running your first simulation
-----------------------------

Now that we've introduced the basics of working with quantum states in SQUANCH, let's start with a simple demonstration that can demonstrate some of the most basic capabilities of SQUANCH. We'll just prepare an ensemble of Bell pairs in the state :math:`\lvert q_1 q_2 \rangle = \frac{1}{\sqrt{2}} \left (\lvert 00 \rangle + \lvert 11 \rangle \right )` and verify that they all collapse to the same states. For this example, all we'll need are the :ref:`qubit <qubit>` and :ref:`gates <gates>` modules. We'll create a new two-particle quantum system in each iteration of the loop, and then apply H and CNOT operators to the system's qubits to make the Bell pair.

.. code:: python

	from squanch.qubit import *
	from squanch.gates import *

	results = [] # Where we'll put the measurement results 

	for _ in range(10):
	    qSys = QSystem(2)
	    a, b = qSys.qubits # enumerate the qubits of the system
	    # Make a Bell pair
	    H(a)
	    CNOT(a, b)
	    # Measure the pair and append to results
	    results.append([a.measure(), b.measure()])

	print results

Running the whole program, we obtain:

.. parsed-literal:: 

	[[0, 0], [1, 1], [0, 0], [1, 1], [0, 0], [1, 1], [0, 0], [0, 0], [1, 1], [0, 0]] 


Introduction to quantum streams
-------------------------------

One of the more unique concepts to SQUANCH comapred to other quantum simulation frameworks is the notion of a "quantum stream", or :ref:`QStream <qstream>`. This is the quantum analogue of a classical bitstream; a collection of disjoint (non-entangled) quantum systems. As before, let's play around with these.

.. code:: python

	from squanch.qstream import *
	from squanch.gates import *

	# Prepare a stream of 3 two-qubit systems
	stream = QStream(2, 3) 

The state of a ``QStream`` is just an array of density matrices, each element of which can be used to instantiate a ``QSystem``:

.. code:: python

	stream.state 

.. parsed-literal::

	array([[[ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j]],

	       [[ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j]],

	       [[ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
	        [ 0.+0.j,  0.+0.j,  0.+0.j,  0.+0.j]]], dtype=complex64)

You can pull specific systems from a stream an manipulate them. For example, let's apply H to the second qubit of the third system in the stream:

.. code:: python

	firstSys = stream.system(2)
	H(firstSys.qubit(1)) 

.. parsed-literal::

	array([[[ 1.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j]],

	       [[ 1.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j]],

	       [[ 0.5+0.j,  0.5+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.5+0.j,  0.5+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j],
	        [ 0.0+0.j,  0.0+0.j,  0.0+0.j,  0.0+0.j]]], dtype=complex64)

You can also iterate over the systems in a stream:

.. code:: python

	for qSys in stream:
	    a, b = qSys.qubits
	    print [a.measure(), b.measure()]

.. parsed-literal::

	[0, 0]
	[0, 0]
	[0, 1]

Using QStreams has a number of advantages: it reduces instantiation overhead, it allows :ref:`Agents <agent>` (which we'll talk about in a bit) to manipulate the same quantum states, and it can vastly increase performance by providing good cache locality. Typical sequential operations operating in a single thread will usually see a performance gain of about 2x, but for simulations involving a large number of Agents in separate processes working on qubits in varying positions in the stream, you may see much larger performance gains.


A simulation with QStreams
--------------------------

Here's a brief demonstration of how to use QStreams in your programs and an example of performance speedups.

.. code:: python

	import time
	from squanch.qstream import *
	from squanch.qubit import *
	from squanch.gates import *

	numSystems = 100000

	# Make a bunch of Bell pairs without using streams
	startNoStream = time.time()
	for _ in range(numSystems):
	    a, b = QSystem(2).qubits
	    H(a)
	    CNOT(a, b)
	print "Creating {} bell pairs without streams: {:.3f}s".format(numSystems, time.time() - startNoStream)

	# Modify all systems in a stream to be Bell pairs
	startStream = time.time()
	stream = QStream(2, numSystems)
	for system in stream:
	    a, b = system.qubits
	    H(a)
	    CNOT(a, b)
	print "Creating {} bell pairs with streams:    {:.3f}s".format(numSystems, time.time() - startStream)

.. parsed-literal::

	Creating 100000 bell pairs without streams: 5.564s
	Creating 100000 bell pairs with streams:    2.355s


Using agents in your simulations
--------------------------------

So far, we've touched on features that mostly have analogues in other quantum computing frameworks. However, SQUANCH is a quantum *networking* simulator, and its core feature set is the ability to easily simulate agents manipulating and transferring quantum inforamtion between each other concurrently. 

An :ref:`Agent <agent>` generalizes the notion of a quantum-classical "actor". Agents are programmed by extending the base Agent class to contain the runtime logic in the ``run()`` function. In simulations, Agents run in separate processes, so it is necessary to explicitly pass in input and output structures, including the shared Hilbert space the Agents act on, and a multiprocessed return dictionary for outputting data from runtime. Both of these are included in the :ref:`Agents <agent>` module.

Here's a demonstration of a simple message tranmsision protocol using qubits as classical bits. There will be two agents, Alice and Bob; Alice will have a message encoded as a bitstream, which she will use to act on her qubits that she will send to Bob, who will reconstruct the original message. Let's start with the preliminary imports and string to bitstream conversion functions:

.. code:: python

	from squanch.agent import *
	from squanch.gates import *

	def stringToBits(msg):
	    # Return a string of 0's and 1's from a message
	    bits = ""
	    for char in msg: bits += "{:08b}".format(ord(char))
	    return bits

	def bitsToString(bits):
	    # Return a message from a binary string
	    msg = ""
	    for i in range(0, len(bits), 8):
	        digits = bits[i:i + 8]
	        msg += chr(int(digits, 2))
	    return msg
	
	message = "Hello, Bob!"
	msgBits = stringToBits(message)

To program the agents themselves, we extend the Agent base class and overwrite the ``run()`` function:

.. code:: python

	class Alice(Agent):
	    def run(self):
	        for qSys, bit in zip(self.stream, self.data):
	            q, = qSys.qubits
	            if bit == "1": X(q)
	            self.qsend(bob, q)


	class Bob(Agent):
	    def run(self):
	        bits = ""
	        for _ in self.stream:
	            q = self.qrecv(alice)
	            bits += str(q.measure())
	        self.output(bits)

Finally, to instantiate and run the agents, we need to make an appropriately sized ``sharedHilbertSpace`` and a ``sharedOutputDict`` to pass to the agents. We then connect the agents (using a channel length of 0 to ignore speed-of-light delays and attenuation errors) and run their processes:

.. code:: python 

	mem = sharedHilbertSpace(1, len(msgBits))
	out = sharedOutputDict()

	alice = Alice("Alice", mem, data = msgBits)
	bob = Bob("Bob", mem, out = out)

	connectAgents(alice, bob, length = 0.0)

	alice.start(); bob.start()
	alice.join(); bob.join()

	receivedMessage = bitsToString(out["Bob"])
	print "Alice sent: '{}'. Bob received: '{}'.".format(message, receivedMessage)

.. parsed-literal::

	Alice sent: 'Hello, Bob!'. Bob received: 'Hello, Bob!'. 

See also
--------

This tutorial page only touches on some very basic uses of SQUANCH. For demonstrations of more complex scenarios, see the :ref:`demonstrations section <demos>`, and for an overview of SQUANCH's core concepts and organization, see the :ref:`overview section <overview>`.
