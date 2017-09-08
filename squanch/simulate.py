import tqdm
import time
import threading


class Simulation:
    '''
    Simulation class for easily creating and running agent-based simulations.
    Includes progress monitors for terminal and Jupyter notebooks.
    '''

    def __init__(self, *args):
        '''
        Initialize the simulation

        :param args: unpacked list of agents, e.g. Simulation(alice, bob, charlie)
        '''
        self.out = args[0].out
        self.agents = args

    def progressMonitor(self, poisonPill):
        '''
        Display a tqdm-style progress bar in a Jupyter notebook

        :param threading.Event poisonPill: a flag to kill the progressMonitor thread
        '''
        pbars = {}
        progress = {}
        progressMax = {}
        for agent in self.agents:
            pbars[agent.name] = tqdm.tqdm_notebook(total = len(agent.stream), desc = agent.name)
            progress[agent.name] = 0
            progressMax[agent.name] = len(agent.stream)

        # Loop and update progress
        while not poisonPill.isSet():
            for agent in self.agents:
                dProg = self.out[agent.name + ":progress"] - progress[agent.name]
                progress[agent.name] += dProg
                pbars[agent.name].update(dProg)
            time.sleep(0.05)

        for agent in self.agents:
            pbars[agent.name].n = pbars[agent.name].total
            pbars[agent.name].close()

    def run(self, monitorProgress = True):
        '''
        Run the simulation

        :param monitorProgress: whether to display a progress bar for each agent
        '''

        for agent in self.agents:
            agent.start()

        if monitorProgress:
            poisonPill = threading.Event()
            progMonitor = threading.Thread(target = self.progressMonitor, args = (poisonPill,))
            progMonitor.start()

        for agent in self.agents:
            agent.join()

        if monitorProgress:
            poisonPill.set()
            progMonitor.join()