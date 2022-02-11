from collections import defaultdict
from src.grid.line import Line
from src.grid.node import Node
from typing import List
import numpy as np


class Grid:
    def __init__(self,
                 name: str,
                 nodes: List[Node],
                 lines: List[Line],
                 ref_index: int = 0,
                 ref_voltage: int = 350,
                 loads_regions: list = None,):

        """ Class for the DC grid. Stores topology, admittance matrix and information about regions
            name: name of the grid
            nodes: list of nodes in the grid
            lines: list of lines between nodes
            ref_index: index of the reference node
            ref_voltage: voltage in the reference node in V
            loads_regions: list of regions, in a format [[n1, n2], [n3, n4], [n5]] """

        self.name = name
        self.nodes = nodes
        self.n_nodes = len(nodes)

        self.lines = lines
        self.n_lines = len(lines)
        self.ref_index = ref_index
        self.ref_voltage = ref_voltage
        self._set_N()
        self._set_node_to_lines()
        self._set_G_and_Y()
        self._set_loads_and_gens()
        self.loads_regions = loads_regions if loads_regions is not None else [[node_ind]
                                                                              for node_ind in range(self.n_nodes)]

    def _set_N(self):
        self.N = defaultdict(list)
        for line in self.lines:
            node_from_ind = self.nodes.index(line.node_from)
            node_to_ind = self.nodes.index(line.node_to)
            self.N[node_from_ind].append(node_to_ind)
            self.N[node_to_ind].append(node_from_ind)

    def _set_node_to_lines(self):
        self.node_to_lines_dict = defaultdict(list)
        self.nodes_to_groups = dict()
        self.lines_to_groups = dict()
        for line_ind, line in enumerate(self.lines):
            node_from_ind = self.nodes.index(line.node_from)
            node_to_ind = self.nodes.index(line.node_to)
            self.node_to_lines_dict[node_from_ind].append(line)
            self.node_to_lines_dict[node_to_ind].append(line)

    def _set_G_and_Y(self):
        self.G = np.zeros((self.n_nodes, self.n_nodes))
        for line in self.lines:
            node_from = line.node_from
            node_to = line.node_to
            self.G[self.nodes.index(node_from), self.nodes.index(node_to)] = line.g
            self.G[self.nodes.index(node_to), self.nodes.index(node_from)] = line.g

        self.Y = -np.copy(self.G)
        for i in range(self.Y.shape[0]):
            self.Y[i, i] = np.sum(self.G[i])

    def _set_loads_and_gens(self):
        self.loads = []
        self.load_inds = []
        self.passives = []
        self.passive_inds = []
        self.gen_inds = []
        self.gens = []

        for n_ind, n in enumerate(self.nodes):
            if n.type == 'load':
                self.loads.append(n)
                self.load_inds.append(n_ind)
            elif n.type == 'gen':
                self.gens.append(n)
                self.gen_inds.append(n_ind)
            elif n.type == 'passive':
                self.passives.append(n)
                self.passive_inds.append(n_ind)

        self.n_loads = len(self.load_inds)
        self.n_gens = len(self.gen_inds)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def get_init_state(self):
        V_nodes = np.array([n.v_nominal for n in self.nodes])
        P_nodes = np.array([0 for _ in self.nodes])
        I_nodes = np.array([0 for _ in self.nodes])
        I_lines = np.array([0 for _ in self.lines])
        return V_nodes, P_nodes, I_nodes, I_lines

    def apply_state(self, V_nodes, P_nodes, I_nodes, I_lines):

        for node_ind, node in enumerate(self.nodes):
            node.v_current = V_nodes[node_ind]
            node.p_current = P_nodes[node_ind]
            node.i_current = I_nodes[node_ind]

        for line_ind, line in enumerate(self.lines):
            node_from = line.node_from
            node_to = line.node_to
            line.v_diff_current = V_nodes[self.nodes.index(node_from)] - V_nodes[self.nodes.index(node_to)]
            line.i_current = I_lines[line_ind]
            line.p_loss_current = line.i_current * line.v_diff_current

    def update_demand_and_price(self, p_demand_min, p_demand_max, utility_coefs):
        for node_ind, node in enumerate(self.nodes):
            node.update_demand(p_demand_min[node_ind], p_demand_max[node_ind], utility_coefs[node_ind])

    def __copy__(self):
        return Grid(self.name + '_unified', self.nodes, self.lines,
                    self.ref_index, self.ref_voltage, self.loads_regions)
