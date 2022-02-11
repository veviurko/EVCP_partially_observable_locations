import numpy as np


class Node:
    def __init__(self,
                 name: str,
                 node_type: str = 'load',
                 v_min: float =300,
                 v_max: float = 400,
                 v_nominal: float = 350,
                 p_min: float = -np.inf,
                 p_max: float = np.inf,
                 i_min: float = -np.inf,
                 i_max: float = np.inf,
                 ):
        """ Node in the grid. Can be load, passive or generator.
            v_min, v_max -- minimum and maximum voltages, in V
            v_nominal -- nominal voltage of the node in V
            p_min, p_max -- minimum and maximum power in the node in W
            i_min, i_max -- minimum and maximum current in the node in A """
        if node_type == 'load':
            self.type = 'load'
        elif node_type in ['gen', 'generator']:
            self.type = 'gen'
        elif node_type in ['passive', 'pas']:
            self.type = 'passive'
        else:
            raise ValueError('Unknown node type %s' % node_type)

        self.name = name

        self.v_min = v_min
        self.v_max = v_max
        self.v_nominal = v_nominal

        self.p_min = p_min
        self.p_max = p_max

        self.p_demand_min = -np.inf
        self.p_demand_max = np.inf

        self.i_min = i_min
        self.i_max = i_max

        self.v_current = v_nominal
        self.p_current = 0
        self.i_current = 0

        self.utility_coef = 0

        if self.type == 'passive':
            self.p_min = -1e-5
            self.p_max = 1e-5
            self.p_demand_min = -1e-5
            self.p_demand_max = 1e-5
            self.i_min = -1e-5
            self.i_max = 1e-5

        self.inv_droop = np.divide((self.i_max - self.i_min), 5)
        self.droop_i0 = 50 - np.multiply(self.inv_droop, self.v_nominal)
        self.droop_i0 = 0

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def update_demand(self, p_demand_min, p_demand_max, utility_coef):
        if self.type != 'passive':
            self.p_demand_min = p_demand_min
            self.p_demand_max = p_demand_max
            self.utility_coef = utility_coef
