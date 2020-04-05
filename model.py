import numpy as np
import pandas as pd


def infectiousness(days_since_infection):
    return 1 if days_since_infection is not None else 0


def immunity(days_since_infection, days_of_immunity=100):
    if days_since_infection is not None:
        return 1 - (days_of_immunity - days_since_infection) / days_of_immunity
    else:
        return 0


def emergence():
    return True


base_infectiousness = 0.05
mortality = 0.01


class Place:
    def __init__(self, name, capacity=10, desirability=1, fullness_aversion_factor=0.1, edges=[], agents=[]):
        self.name = name
        self.capacity = capacity
        self.desirability = desirability
        self.edges = edges
        self.agents = agents
        self.fullness_aversion_factor = fullness_aversion_factor

    def fullness_aversion_score(self):
        return max(1 - self.fullness_aversion_factor * len([a for a in self.agents if a.live]) / self.capacity, 0)

    def has_capacity(self):
        return self.capacity > len([a for a in self.agents if a.live])

    def evolve(self):
        hazard = 1 - self.fullness_aversion_score()
        for agent in self.agents:
            for contra in self.agents:
                if contra.live:
                    agent.contact(contra, hazard=hazard)


class World:
    def __init__(self, randomize=True):
        self.places = []
        self.agents = []
        self.graph = {}

        if randomize:
            self._randomize()

    def _randomize(self, n_places=100, n_agents=1000):

        # Create several random places
        for i in range(n_places):
            new_place = Place(name='P{}'.format(i),
                              capacity=np.random.randint(
                                  (n_agents / n_places) * 0.2, (n_agents / n_places) * 2),
                              desirability=np.random.rand(),
                              fullness_aversion_factor=np.random.rand())
            self.places.append(new_place)

        # Confirm the world has capacity for all of the agents we are creating
        while(np.sum([p.capacity for p in self.places]) < n_agents):
            # Choose a random place and bolster its capacity
            chosen_place = np.random.choice(self.places)
            chosen_place.capacity += 1

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
            new_agent = Agent(name='A{}'.format(i), p_move=np.random.rand())
            self.add_agent(new_agent)

        self._force_emergence()

        return True

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
            placed = False
            for place in np.random.permutation(self.places):
                if place.has_capacity():
                    destination = place
                    placed = True
                    break
            if not placed:
                raise Exception('Could not assign agent {}'.format(agent.name))

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

    def evolve(self):
        # First, move everybody to their new places
        for agent in self.agents:
            self._move_agent_to_place(agent, agent.next_destination())

        # Second, evolve the properties of each place
        for place in self.places:
            place.evolve()

        # Finally, evolve disease states
        for agent in self.agents:
            agent.evolve()

    def _force_emergence(self):
        chosen_agent = np.random.choice(self.agents)
        chosen_agent.infect()

    def census(self):
        population = pd.Series(name='population')
        infected = pd.Series(name='infected')
        immune = pd.Series(name='immune')
        susceptible = pd.Series(name='susceptible')
        cured = pd.Series(name='cured')

        for place in self.places:
            l = str(place.name)
            population[l] = len(
                [a for a in place.agents if a.live])

            infected[l] = len(
                [a for a in place.agents if a.infected])

            immune[l] = len(
                [a for a in place.agents if a.immunity > 0])

            susceptible[l] = population[l] - immune[l]
            cured[l] = immune[l] - infected[l]

        df = pd.concat(
            [population.to_frame().T, infected.to_frame().T,
             immune.to_frame().T, susceptible.to_frame().T, cured.to_frame().T]
        )

        return df


class Agent:
    def __init__(self, name, place=None, p_move=0.2):
        self.place = place
        self.name = name
        self.p_move = p_move

        # Infection properties
        self.infected = False
        self.live = True
        self.days_since_infection = None
        self.infectiousness = 0
        self.immunity = 0       # Immunity post-infection
        self.resistance = 0.5   # Base immunity pre-infection

    def contact(self, contra, hazard=1):
        # First, evaluate how likely this agent is to become infected
        if self.live and contra.live:
            infectiousness_score = contra.infectiousness * hazard * base_infectiousness
            resistance_score = self.resistance * self.immunity
            if infectiousness_score > resistance_score:
                self.infect()

        return self.infected

    def evolve(self):
        # Get the infection state of the agent

        if self.infected and (np.random.rand() < mortality):
            self.live = False
            self.infected = False
            self.immunity = 0
            self.infectiousness = 0
            self.p_move = 0

        if self.live:
            if self.infected:
                self.infectiousness = infectiousness(self.days_since_infection)
                self.days_since_infection += 1

            self.immunity = immunity(self.days_since_infection)

            # Agent becomes cured
            if self.infected and (self.immunity > 0.1):
                self.cure()

        return None

    def cure(self):
        self.infected = False

    def infect(self):
        self.infected = True
        self.days_since_infection = 0

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
