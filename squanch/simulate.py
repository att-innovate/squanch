import tqdm
import time
import threading

__all__ = ["Simulation"]


class Simulation:
    '''
    Simulation class for easily creating and running agent-based simulations.
    Includes progress monitors for terminal and Jupyter notebooks.
    '''

    # noinspection PyUnresolvedReferences
    def __init__(self, *args):
        '''
        Initialize the simulation

        :param args: unpacked list of agents, e.g. Simulation(alice, bob, charlie). All agents must share the same
                     output dictionary using Agent.shared_output()
        '''
        self.out = args[0].out
        self.agents = args
        try:  # figure out if we're in a Jupyter notebook or not
            __IPYTHON__
            self.is_ipython = True
        except:
            self.is_ipython = False

    def progress_monitor(self, poison_pill):
        '''
        Display a tqdm-style progress bar in a Jupyter notebook

        :param threading.Event poison_pill: a flag to kill the progressMonitor thread
        '''
        pbars = {}
        progress = {}
        progress_max = {}
        for agent in self.agents:
            if self.is_ipython:
                pbars[agent.name] = tqdm.tqdm_notebook(total = len(agent.stream), desc = agent.name)
            else:
                pbars[agent.name] = tqdm.tqdm(total = len(agent.stream), desc = agent.name)
            progress[agent.name] = 0
            progress_max[agent.name] = len(agent.stream)

        # Loop and update progress
        while not poison_pill.isSet():
            for agent in self.agents:
                dProg = self.out[agent.name + ":progress"] - progress[agent.name]
                progress[agent.name] += dProg
                pbars[agent.name].update(dProg)
            time.sleep(0.05)

        for agent in self.agents:
            pbars[agent.name].n = pbars[agent.name].total
            pbars[agent.name].close()

    # noinspection PyUnboundLocalVariable
    def run(self, monitor_progress = True):
        '''
        Run the simulation

        :param monitor_progress: whether to display a progress bar for each agent
        '''

        for agent in self.agents:
            agent.start()

        if monitor_progress:
            poison_pill = threading.Event()
            progress_monitor = threading.Thread(target = self.progress_monitor, args = (poison_pill,))
            progress_monitor.start()

        for agent in self.agents:
            agent.join()

        if monitor_progress:
            poison_pill.set()
            progress_monitor.join()
