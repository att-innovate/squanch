.. _quantumErrorCorrectionDemo:

Quantum Error Correction
========================

When qubits are transmitted over quantum channels, they are subject to a complex set of errors which can cause them to decohere, depolarize, or simply vanish completely. For quantum information transfer to be feasible, the information must be encoded in a error-resistent format using any of a variety of quantum error correction models. In this demonstration, we show how to use SQUANCH's channel and error modules to simulate quantum errors in a transmitted message, which we correct for using the `Shor Code <https://en.wikipedia.org/wiki/Quantum_error_correction#The_Shor_code>`_ This error correction model encodes a single logical qubit into the product of 9 physical qubits and is capable of correcting for arbitrary single-qubit errors. A circuit diagram of the protocol we will implement is shown below, where $E$ represents a quantum channel which can arbitrarily corrupt a single qubit:

.. image:: https://upload.wikimedia.org/wikipedia/commons/a/a9/Shore_code.svg

Protocol
--------

	1. Alice has some state :math:`|\psi\rangle=\alpha_0|0\rangle+\alpha_1|1\rangle`, which she wants to send to Bob through a noisy quantum channel. She encodes her state as :math:`|\psi \rangle \rightarrow \alpha_0 \frac{1}{2\sqrt{2}}(|000\rangle + |111\rangle) \otimes (|000\rangle + |111\rangle) \otimes (|000\rangle + |111\rangle) + \alpha_1\frac{1}{2\sqrt{2}}(|000\rangle - |111\rangle) \otimes (|000\rangle - |111\rangle) \otimes (|000\rangle - |111\rangle)` using the circuit diagram above.

    2. DumbAlice wants to do the same, but doesn't encode her state.

	3. Alice and DumbAlice send their qubits through the quantum channel to Bob and DumbBob, respectively. The channel may apply an arbitrary unitary operation to a single physical qubit in each group of 9.

	4. Bob and DumbBob receive their qubits. Bob decodes his using the Shor decoding circuit. DumbBob is dumb, and thus does nothing. For the purposes of this demonstration, the qubits will be measured and the results assembled to form a message.

Implementation
--------------

.. code:: python

    from squanch import *
    from scipy.stats import unitary_group
    import copy
    import numpy as np
    import matplotlib.image as image
    import matplotlib.pyplot as plt

First, let's define what each of the agents do. Let's start with Alice and DumbAlice.

.. code:: python

    class Alice(Agent):
        '''Alice sends an arbitrary Shor-encoded state to Bob'''
        def shor_encode(self, qsys):
            # psi is state to send, q1...q8 are ancillas from top to bottom in diagram
            psi, q1, q2, q3, q4, q5, q6, q7, q8 = qsys.qubits
            # Gates are enumerated left to right, top to bottom from figure
            CNOT(psi, q3)
            CNOT(psi, q6)
            H(psi)
            H(q3)
            H(q6)
            CNOT(psi, q1)
            CNOT(psi, q2)
            CNOT(q3, q4)
            CNOT(q3, q5)
            CNOT(q6, q7)
            CNOT(q6, q8)
            return psi, q1, q2, q3, q4, q5, q6, q7, q8

        def run(self):
            for qsys in self.stream:
                # send the encoded qubits to Bob
                for qubit in self.shor_encode(qsys):
                    self.qsend(bob, qubit)

    class DumbAlice(Agent):
        '''DumbAlice sends a state to Bob but forgets to error-correct!'''
        def run(self):
            for qsys in self.stream:
                for qubit in qsys.qubits:
                    self.qsend(dumb_bob, qubit)

Now let's define Bob's behavior:

.. code:: python

    class Bob(Agent):
        '''Bob receives Alice's qubits and applied error correction'''
        def shor_decode(self, psi, q1, q2, q3, q4, q5, q6, q7, q8):
            # same enumeration as Alice
            CNOT(psi, q1)
            CNOT(psi, q2)
            TOFFOLI(q2, q1, psi)
            CNOT(q3, q4)
            CNOT(q3, q5)
            TOFFOLI(q5, q4, q3)
            CNOT(q6, q7)
            CNOT(q6, q8)
            TOFFOLI(q7, q8, q6) # Toffoli control qubit order doesn't matter
            H(psi)
            H(q3)
            H(q6)
            CNOT(psi, q3)
            CNOT(psi, q6)
            TOFFOLI(q6, q3, psi)
            return psi # psi is now the original state

        def run(self):
            measurement_results = []
            for _ in self.stream:
                # Bob receives 9 qubits representing Alice's encoded state
                received = []
                for i in range(9):
                    q = self.qrecv(alice)
                    received.append(q)
                # Decode and measure the original state
                psi_true = self.shor_decode(*received)
                measurement_results.append(psi_true.measure())
            self.output(measurement_results)

    class DumbBob(Agent):
        '''DumbBob receives a state from Alice but does not error-correct'''
        def run(self):
            measurement_results = []
            for _ in self.stream:
                received = []
                for i in range(9):
                    received.append(self.qrecv(dumb_alice))
                psi_true = received[0]
                measurement_results.append(psi_true.measure())
            self.output(measurement_results)

Now we need to make an error model to simulate the qubit corruption. SQUANCH includes base classes for defining error models and quantum/classical channels. In this demonstration, we'll only use a quantum error, from the base class ``QError``, and a quantum channel model, from the base class ``QChannel``. Let's start with the error model, which can apply a random unitary operation to a single qubit in each group of nine.

.. code:: python

    class ShorError(QError):

        def __init__(self, qchannel):
            '''
            Instatiate the error model from the parent class
            :param QChannel qchannel: parent quantum channel
            '''
            QError.__init__(self, qchannel)
            self.count = 0 # tracks which qubit out of 9 we're at
            self.error_applied = False # if another error can be applied

        def apply(self, qubit):
            '''
            Apply a random unitary operation to one of the qubits in a set of 9
            :param Qubit qubit: qubit from quantum channel
            :return: either unchanged qubit or None
            '''
            # qubit could be None if combining with other error models, such as attenuation
            if not self.error_applied and qubit is not None:
                if np.random.rand() < 0.5: # apply the error
                    random_unitary = unitary_group.rvs(2) # pick a random U(2) matrix
                    qubit.apply(random_unitary)
                    self.error_applied = True
            # update count and reset error if necessary
            self.count += 1
            if self.count >= 9:
                self.count = self.count % 9
                self.error_applied = False
            return qubit

Adding this error to a channel model is simple: simply call ``__init__`` of the parent channel class and add the error class to the ``self.errors`` list:

.. code:: python

    class ShorQChannel(QChannel):
        '''Represents a quantum channel with the Shor error applied'''

        def __init__(self, from_agent, to_agent):
            QChannel.__init__(self, from_agent, to_agent)
            # register the error model
            self.errors = [ShorError(self)]

Before we move on, let's make some helper functions:

.. code:: python

    def to_bits(string):
        '''Convert a string to a list of bits'''
        result = []
        for c in string:
            bits = bin(ord(c))[2:]
            bits = '00000000'[len(bits):] + bits
            result.extend([int(b) for b in bits])
        return result

    def from_bits(bits):
        '''Convert a list of bits to a string'''
        chars = []
        for b in range(int(len(bits) / 8)):
            byte = bits[b*8:(b+1)*8]
            chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
        return ''.join(chars)

Now let's prepare a set of states for Alice to transmit to Bob. Since each qsystem has 9 qubits -- much larger than in the other demonstrations -- we don't want to make anything too large, so a small text message is suitable.

.. code:: python

    # Prepare a message to send
    msg = "Peter Shor once lived in Ruddock 238! But who was Airman?"
    bits = to_bits(msg)

    # Allocate memory and output
    mem = Agent.shared_hilbert_space(9, len(bits)) # 9 qubits per encoded state
    out = Agent.shared_output()

    # Encode the message as spin eigenstates
    stream = QStream.from_array(mem)
    for bit, qsystem in zip(bits, stream):
        q = qsystem.qubit(0)
        if bit == 1:
            X(q)

Finally, we need to instantiate Alice, DumbAlice, Bob, and DumbBob. We'll make a copy of ``mem`` for DumbAlice and DumbBob to use since they can't be trusted with the real thing. (Otherwise, manipulations done by DumbAlice would affect Bob's memory/QStream/qubits.)

.. code:: python

	# Alice and Bob will use error correction
    alice = Alice(mem, out)
    bob = Bob(mem, out)
    alice.qconnect(bob, ShorQChannel)

    # Dumb agents won't use error correction
    mem2 = copy.deepcopy(mem)
    dumb_alice = DumbAlice(mem2, out)
    dumb_bob = DumbBob(mem2, out)
    dumb_alice.qconnect(dumb_bob, ShorQChannel)

Finally, let's run the simulation!

.. code:: python

	# Run everything and record results
    Simulation(dumb_alice, dumb_bob, alice, bob).run()
    print("DumbAlice sent:   {}".format(msg))
    print("DumbBob received: {}".format(from_bits(out["DumbBob"])))
    print("")
    print("Alice sent:       {}".format(msg))
    print("Bob received:     {}".format(from_bits(out["Bob"])))

.. parsed-literal::



Source code
-----------

The full source code for this demonstration is available in the demos directory of the SQUANCH repository.
