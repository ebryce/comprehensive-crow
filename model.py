import numpy as np


class Place:
    def __init__(self, name, capacity=10, desirability=1, fullness_aversion_factor=0.1, edges=[], agents=[]):
        self.name = name
        self.__name__ = name
        self.capacity = capacity
        self.desirability = desirability
        self.edges = edges
        self.agents = agents
        self.fullness_aversion_factor = fullness_aversion_factor

    def fullness_aversion_score(self):
        return 1 - self.fullness_aversion_factor * len(self.agents) / self.capacity

    def evolve(self):
        return None


class World:
    def __init__(self, randomize=True):
        self.places = []
        self.agents = []
        self.graph = {}

        if randomize:
            self._randomize()

    def _randomize(self, n_places=10, n_agents=20):

        # Create several random places
        for i in range(n_places):
            new_place = Place(name=i,
                              capacity=np.random.randint(2, 10),
                              desirability=np.random.rand(),
                              fullness_aversion_factor=np.random.rand())
            self.places.append(new_place)

        # Create a randomly connected graph of places
        for place in self.places:
            n_connections = np.random.randint(1, 3)
            n_existing_connections = 0
            for other_place in self.places:
                if place in other_place.edges:
                    n_existing_connections += 1

            n_new_connections = n_connections - n_existing_connections

            if n_new_connections > 0:
                place.edges = list(np.random.permutation(
                    self.places)[:n_new_connections])

        self.regraph()

        # Create several random agents
        for i in range(n_agents):
            new_agent = Agent(name=i, p_move=np.random.rand())
            self.add_agent(new_agent)

    def _add_place(self, place):
        # Base function for adding places
        self.places.append(place)
        self.regraph()

    def _add_agent(self, agent):
        # Base function for adding agents
        self.agents.append(agent)

        # Randomly assign this agent to a place
        self._assign_agent_to_initial_place(agent, destination=agent.place)

    def _assign_agent_to_initial_place(self, agent, destination=None):

        for place in self.places:
            if agent.name in [a.name for a in place.agents]:
                return None

        if destination == None:
            # Randomly assign the agent to a place
            for place in np.random.permutation(self.places):
                if place.fullness_aversion_score() > 0:
                    destination = place
                    break

        self._move_agent_to_place(agent=agent, destination=destination)

    def _move_agent_to_place(self, agent, destination):
        # Remove agent from other previous places they may have been
        for place in self.places:
            if (agent in place.agents):
                place.agents.remove(agent)

        agent.place = destination
        if agent not in destination.agents:
            destination.agents = destination.agents + [agent]

    def add_place(self, place):
        # Nice handler function for adding places
        if type(place) == Place:
            self._add_place(place)
        elif type(place) == list:
            for p in place:
                self._add_place(p)
        else:
            raise Exception('Cannot add non-place to world')

    def add_agent(self, agent):
        # Nice handler function for addint agents
        if type(agent) == Agent:
            self._add_agent(agent)
        elif type(agent) == list:
            for a in agent:
                self._add_agent(a)
        else:
            raise Exception('Cannot add non-agent to world')

    def regraph(self):
        # Rebuild the place network
        self.graph = {}
        for place in self.places:
            # For each place, make sure it is connected to its neighbours
            self.graph[place] = place.edges

            # Iterate through all of the neighbours
            for edge in place.edges:
                # Ensure all neighbours are connected to this place
                if place not in edge.edges:
                    edge.edges.append(place)

                # Confirm this is reflected in the graph
                if edge in self.graph:
                    # If the neighbour is already in the graph
                    if place not in self.graph[edge]:
                        # Connect the neighbour to this place
                        self.graph[edge].append(place)
                else:
                    # If the neighbour is not already in the graph
                    self.graph[edge] = [place]

        # Rebuild each of the individual place edge maps
        for place in self.places:
            place.edges = self.graph[place]

    def walk(self):

        # First, move everybody to their new places
        for agent in self.agents:
            self._move_agent_to_place(agent, agent.next_destination())

        # Second, evolve the properties of each place
        for place in self.place:
            place.evolve()

    def census(self):
        population = {}
        for place in self.places:
            population[place.name] = len(place.agents)
        return population


class Agent:
    def __init__(self, name, place=None, p_move=0.2):
        self.place = place
        self.name = name
        self.p_move = p_move

    def evolve(self):
        return None

    def next_destination(self):
        destination = self.place
        if np.random.rand() > self.p_move:
            place_scores = {}

            # Score how likely the agent is to go to some adjacent place
            for edge in self.place.edges + [self.place]:
                place_score = edge.desirability * edge.fullness_aversion_score() * \
                    np.random.rand()

                place_scores[edge] = place_score

            # Choose the optimal place for this agent to go to
            for place in place_scores:
                if place_scores[place] > place_scores[destination]:
                    destination = place
        return destination


class Model:
    def __init__(self, world):
        model.world = world
