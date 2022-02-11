from pyomo.environ import ConcreteModel
import numpy as np
import itertools


def read_model(model: ConcreteModel):

    """ Read the solution of the OPF problem """

    def _dict_to_matrix(d, *indices):
        res = np.empty(list(len(inds) for inds in indices))
        for ind in itertools.product(*indices):
            if callable(d[ind]):
                res[ind] = d[ind]()
            else:
                res[ind] = d[ind]
        return res

    V_nodes = _dict_to_matrix(model.V_nodes, model.nodes.data()) * model.norm_factor
    P_nodes = _dict_to_matrix(model.P_nodes, model.nodes.data()) * model.norm_factor ** 2
    I_nodes = P_nodes / V_nodes
    I_lines = _dict_to_matrix(model.I_lines, model.lines.data()) * model.norm_factor
    return V_nodes, P_nodes, I_nodes, I_lines
