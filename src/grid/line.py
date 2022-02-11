from src.grid.node import Node
import numpy as np


class Line:
    def __init__(self,
                 node_from: Node,
                 node_to: Node,
                 i_max: float = 1000,
                 g: float = 30):

        """ Line between two nodes.
            i_max -- capacity, in A
            g -- conductance, in S """

        self.node_from = node_from
        self.node_to = node_to
        self.g = g

        self.i_max = i_max
        self.i_min = -i_max

        self.i_current = 0
        self.v_diff_current = 0
        self.p_loss_current = 0
