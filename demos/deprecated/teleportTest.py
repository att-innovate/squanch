from squanch.agent import *
from squanch.gates import *
from squanch.qstream import *

class Alice(Agent):
    '''Alice sends qubits to Bob using a shared Bell pair'''
    def run(self):
        for qSys in self.stream:
            # Generate a Bell pair and send half of it to Bob
            q, a, b = qSys.qubits
            H(a)
            CNOT(a, b)
            self.qsend(bob, b)

            # Perform the teleportation
            CNOT(q, a)
            H(q)
            bobZ = q.measure()
            bobX = a.measure()
            self.csend(bob, [bobX, bobZ])

class Bob(Agent):
    '''Bob receives qubits from Alice and measures the results'''
    def run(self):
        results = []
        for _ in range(self.stream.numSystems):
            b = self.qrecv(alice)
            doX, doZ = self.crecv(alice)
            if doX == 1 and b is not None: X(b)
            if doZ == 1 and b is not None: Z(b)
            results.append(b.measure())
        self.output(results)

# Allocate memory and output structures
mem = sharedHilbertSpace(3, 10)
out = sharedOutputDict()

# Prepare the initial states
stream = QStream.fromArray(mem)
states = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
for qSys, state in zip(stream, states):
    if state == 1: X(qSys.qubit(0))  # Flip the qubits corresponding to 1's

# Make the agents
alice = Alice("Alice", mem)
bob = Bob("Bob", mem, out = out)
connectAgents(alice, bob, length = 0.0)

# Run everything
alice.start(); bob.start()
alice.join(); bob.join()

print out["Bob"]