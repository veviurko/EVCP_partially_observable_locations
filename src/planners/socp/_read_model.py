import numpy as np


def read_model(M, surrogate_grid):
    P_nodes_list = []
    V_nodes_list = []
    SOC_evs_list = []

    P_evs_now = M.getVariable('P_evs_now').level() * M.norm_factor ** 2
    P_nodes_now = M.getVariable('P_nodes_now').level() * M.norm_factor ** 2
    P_nodes_now = P_nodes_now.reshape(M.getVariable('P_nodes_now').getShape())
    V_sq_nodes_now = M.getVariable('V_sq_nodes_now').level()
    V_sq_nodes_now = V_sq_nodes_now.reshape(M.getVariable('V_sq_nodes_now').getShape())
    V_nodes_now = np.sqrt(V_sq_nodes_now) * M.norm_factor
    I_nodes_now = P_nodes_now / V_nodes_now
    I_sq_lines_list = []
    I_sq_lines_neg_list = []
    I_lines_now = np.empty(surrogate_grid.n_lines)
    for line_ind, line in enumerate(surrogate_grid.lines):
        i = surrogate_grid.nodes.index(line.node_from)
        j = surrogate_grid.nodes.index(line.node_to)
        I_lines_now[line_ind] = line.g * (V_nodes_now[i] - V_nodes_now[j])

    for sc_ind in range(M.n_scenarios):
        P_nodes_sc = M.getVariable('P_nodes_sc%d' % sc_ind).level() * M.norm_factor ** 2
        P_nodes_sc = P_nodes_sc.reshape(M.getVariable('P_nodes_sc0').getShape())

        V_sq_nodes_sc = M.getVariable('V_sq_nodes_sc%d' % sc_ind).level()
        V_sq_nodes_sc = V_sq_nodes_sc.reshape(M.getVariable('V_sq_nodes_sc%d' % sc_ind).getShape())
        V_nodes_sc = np.sqrt(V_sq_nodes_sc) * M.norm_factor

        SOC_evs_sc = M.getVariable('SOC_evs_sc%d' % sc_ind).level() * M.norm_factor ** 2
        SOC_evs_sc = SOC_evs_sc.reshape(M.getVariable('SOC_evs_sc%d' % sc_ind).getShape())

        P_nodes_list.append(P_nodes_sc.T)
        V_nodes_list.append(V_nodes_sc.T)
        SOC_evs_list.append(SOC_evs_sc.T)

    '''P_nodes = np.mean(P_nodes_list, 0)
    V_nodes = np.mean(V_nodes_list, 0)
    I_nodes = P_nodes / V_nodes

    I_lines = np.empty((surrogate_grid.n_lines, P_nodes.shape[1]))
    for line_ind, line in enumerate(surrogate_grid.lines):
        i = surrogate_grid.nodes.index(line.node_from)
        j = surrogate_grid.nodes.index(line.node_to)
        I_lines[line_ind] = line.g * (V_nodes[i] - V_nodes[j])
    SOC_evs = np.mean(SOC_evs_list, 0)

    n_evs_to_pad = M.n_evs - len(M.SOC_evs_current)

    if n_evs_to_pad > 0:
        SOC_evs_current_rs = np.pad(M.SOC_evs_current, (0, n_evs_to_pad), constant_values=-42).reshape(-1, 1)
    else:
        SOC_evs_current_rs = M.SOC_evs_current.reshape(-1, 1)
        SOC_evs = np.pad(SOC_evs, ((0, -n_evs_to_pad), (0, 0)), constant_values=-42)

    P_nodes = np.pad(np.concatenate([P_nodes_now.reshape(-1, 1), P_nodes], 1), ((0, 0), (M.t_current_ind, 0)))
    V_nodes = np.pad(np.concatenate([V_nodes_now.reshape(-1, 1), V_nodes], 1), (M.t_current_ind, 0))
    I_nodes = np.pad(np.concatenate([I_nodes_now.reshape(-1, 1), I_nodes], 1), (M.t_current_ind, 0))
    I_lines = np.pad(np.concatenate([I_lines_now.reshape(-1, 1), I_lines], 1), (M.t_current_ind, 0))
    SOC_evs = np.pad(np.concatenate([SOC_evs_current_rs, SOC_evs], 1), (M.t_current_ind, 0))'''

    return P_evs_now, P_nodes_list, V_nodes_list, SOC_evs_list
    #return V_nodes, P_nodes, I_nodes, I_lines, SOC_evs
