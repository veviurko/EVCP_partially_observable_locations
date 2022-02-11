import numpy as np
import itertools


def dict_to_matrix(d, *indices):
    res = np.empty(list(len(inds) for inds in indices))
    for ind in itertools.product(*indices):
        if callable(d[ind]):
            res[ind] = d[ind]()
        else:
            res[ind] = d[ind]
    return res


def read_model(M, surrogate_grid):
    P_evs_now = dict_to_matrix(M.P_evs_now, M.evs.data()) * M.norm_factor ** 2
    P_nodes_now = dict_to_matrix(M.P_nodes_now, M.nodes.data()) * M.norm_factor ** 2
    return P_evs_now, P_nodes_now
