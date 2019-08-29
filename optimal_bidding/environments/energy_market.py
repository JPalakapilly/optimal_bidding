import numpy as np

"""Energy Market Environment"""


class EnergyMarket():
    def __init__(self):
        pass

    def step(self):
        """Collects everyone bids and compute the dispatch
        """
        pass


class Agent():
    """Agent parent class, all the other ch
    """
    def __init__(self):
        pass

    def bid(self, time_step=0):
        """Computes the bid at certain time step

        Args:
          time_step: timestamp UTC

        Return:
          bid: Bid object
        """
        pass

class PVAgent(Agent):
    def __init__(self):
        super().__init__()

    def sample_next_state_from_transition_matrix(self, previous_bid, hour):
        """ return the value for the next bid by sampling from transition matrix

        previous_bid: what the last bid was 
        hour: which hour we are sampling for 
        """


    #1. load the heat map 

        PVTransitionMap = TransitionMap("PV")
        PV_hour_map = PVTransitionMap.get_transition_map_hour[hour]

    #2. Determine the place where it was for the last timestep 
        bids = list(PV_hour_map.columns)
        bid_probabilities = PV_hour_map.loc[previous_bid] # need to test this

    #3. Sample a jump to the next state 
        nextState = np.random.choice(elements, p=bid_probabilities)
        return nextState

    def state_to_bid(hour):
        ## will fill this out when the Bid class is more filled out 
        Bid.power()= sample_generation(hour)

        pass

    def sample_generation(hour):
        """samples a day of solar generation from a year; see utils 
        fuction sample_day_solar_generation(month) for more info

        Currently assumes that we'll stick with a single month. 

        """
        generation_curve = sample_day_solar_generation(6)
        return generation_curve["kW"][hour]



class Bid():
    """Bid object so all bids have the same format
    """
    def __init__(self):
        self._agent_id = None

    def power(self):
        pass

class TraditionalGenco():
    """
    Genco agent that follows the model given in the actor critic paper
    """


    def __init__(self, a=0, b=3.0, c=.03, startup_cost=50, capacity=100):
        super().init()
        self.a = a
        self.b = b
        self.c = c
        self.startup_cost = startup_cost
        self.capacity = capacity

    def set_cost_curve_coefficients(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


    def set_startup_cost(self, startup_cost):
        self.startup_cost = startup_cost


    def cost_curve(self, U):
        return a + b * U + c * U**2


    def bid(self, time_step=0, bid_parts=3):
        """Computes the bid at certain time step

        Args:
          time_step: timestamp UTC

        Return:
          bid: Bid object
        """

        # if preferences don't just do random sampling
        # TODO
        if self.preferences:
            pass
        else:
            bid_set = self.create_bid_set(3)
            r = np.random.randint(len(bid_set))
            bid_prices = bid_set[r]
            # TODO get power points and return

            


    def create_bid_set(self, bid_parts):
        """
        Creates the price part of the bid set as defined in the actor-critic genco paper. 
        
        Parameters
        ----------
        bid_parts: int
            The capacity will be split into bid_parts parts each with a different bid price

        Returns
        -------
        bid_set: Nxbid_parts array
            Each row in this array represents a possible bid. The ith column in the array
            represents the price for the ith part of the capacity.
            N = 3**bid_parts

        """

        part_capacity = self.capacity / bid_parts


        cost_list = []
        for i in range(bid_parts):
            # upper end of cost curve
            m_cost = self.cost_curve(part_capacity * (i+1))

            # get high and low costs
            h_cost = 1.1 * m_cost
            l_cost = .9  * m_cost
            
            cost_list.append(np.array([l_cost, m_cost, h_cost]))

        bid_set = np.array(np.meshgrid(*cost_list)).T.reshape(-1,len(cost_list))
        return bid_set
