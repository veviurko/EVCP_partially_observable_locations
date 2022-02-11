from pyomo.environ import *


def create_variables(M, p_min_arr, p_max_arr, p_evs_min_arr, p_evs_max_arr, v_min_arr,
                     v_max_arr, i_min_arr, i_max_arr, soc_min_arr, soc_max_arr,):

    M.V_nodes_now = Var(M.nodes, )
    # bounds=(v_min_arr[0, M.t_current_ind], v_max_arr[0, M.t_current_ind]))
    M.P_nodes_now = Var(M.nodes, )
    # bounds=(p_min_arr[0, M.t_current_ind], p_max_arr[0, M.t_current_ind]))
    M.I_lines_now = Var(M.lines, )
    # bounds=(i_min_arr[0, M.t_current_ind], i_max_arr[0, M.t_current_ind]))
    M.P_evs_now = Var(M.evs, )
    # bounds=(p_evs_min_arr[0, M.t_current_ind], p_evs_max_arr[0, M.t_current_ind]))
    for node_ind in M.nodes:
        M.V_nodes_now[node_ind].setlb(v_min_arr[0, M.t_current_ind, node_ind])
        M.V_nodes_now[node_ind].setub(v_max_arr[0, M.t_current_ind, node_ind])
        M.P_nodes_now[node_ind].setlb(p_min_arr[0, M.t_current_ind, node_ind])
        M.P_nodes_now[node_ind].setub(p_max_arr[0, M.t_current_ind, node_ind])
        # ub = p_max_arr[0, M.t_current_ind, :]
        #print('node ind % d' % node_ind, 'UB', ub)
    for line_ind in M.lines:
        M.I_lines_now[line_ind].setlb(i_min_arr[0, M.t_current_ind, line_ind])
        M.I_lines_now[line_ind].setub(i_max_arr[0, M.t_current_ind, line_ind])
    for ev_ind in M.evs:
        M.P_evs_now[ev_ind].setlb(p_evs_min_arr[0, M.t_current_ind, ev_ind])
        M.P_evs_now[ev_ind].setub(p_evs_max_arr[0, M.t_current_ind, ev_ind])

    M.V_nodes_sc = Var(M.scenarios, M.timesteps_future, M.nodes,)
    # bounds=(v_min_arr[:, M.t_current_ind + 1:],  v_max_arr[:, M.t_current_ind + 1:]))
    M.P_nodes_sc = Var(M.scenarios, M.timesteps_future, M.nodes,)
    # bounds=(p_min_arr[:, M.t_current_ind + 1:], p_max_arr[:, M.t_current_ind + 1:]))
    M.I_lines_sc = Var(M.scenarios, M.timesteps_future, M.lines,)
    # bounds=(i_min_arr[:, M.t_current_ind + 1:], i_max_arr[:, M.t_current_ind + 1:]))
    M.P_evs_sc = Var(M.scenarios, M.timesteps_future, M.evs,)
    # bounds=(p_evs_min_arr[:, M.t_current_ind + 1:], p_evs_max_arr[:, M.t_current_ind + 1:]))
    M.SOC_evs_sc = Var(M.scenarios, M.timesteps_future, M.evs,)
    # bounds=(soc_min_arr[:, M.t_current_ind + 1:],soc_max_arr[:, M.t_current_ind + 1:]))
    # return V_nodes_now, P_nodes_now, I_lines_now, P_evs_now, V_nodes_sc, P_nodes_sc, I_lines_sc, P_evs_sc, SOC_sc
    for sc_ind in range(M.n_scenarios):
        for t_ind_true in M.timesteps_future:
            t_ind = t_ind_true - M.t_current_ind - 1
            for node_ind in M.nodes:
                M.V_nodes_sc[sc_ind, t_ind_true, node_ind].setlb(v_min_arr[sc_ind, t_ind_true, node_ind])
                M.V_nodes_sc[sc_ind, t_ind_true, node_ind].setub(v_max_arr[sc_ind, t_ind_true, node_ind])
                M.P_nodes_sc[sc_ind, t_ind_true, node_ind].setlb(p_min_arr[sc_ind, t_ind_true, node_ind])
                M.P_nodes_sc[sc_ind, t_ind_true, node_ind].setub(p_max_arr[sc_ind, t_ind_true, node_ind])
            for line_ind in M.lines:
                M.I_lines_sc[sc_ind, t_ind_true, line_ind].setlb(i_min_arr[sc_ind, t_ind_true, line_ind])
                M.I_lines_sc[sc_ind, t_ind_true, line_ind].setub(i_max_arr[sc_ind, t_ind_true, line_ind])
            for ev_ind in M.evs:
                M.P_evs_sc[sc_ind, t_ind_true, ev_ind].setlb(p_evs_min_arr[sc_ind, t_ind_true, ev_ind])
                M.P_evs_sc[sc_ind, t_ind_true, ev_ind].setub(p_evs_max_arr[sc_ind, t_ind_true, ev_ind])
                M.SOC_evs_sc[sc_ind, t_ind_true, ev_ind].setlb(soc_min_arr[sc_ind, t_ind_true, ev_ind])
                M.SOC_evs_sc[sc_ind, t_ind_true, ev_ind].setub(soc_max_arr[sc_ind, t_ind_true, ev_ind])
