import numpy as np


def create_bounds(M, surrogate_grid, scenarios):
    # V2G is not allowed
    p_min_arr, p_max_arr = np.zeros((2, M.n_scenarios, M.n_timesteps, M.n_nodes), dtype='double')
    p_evs_min_arr, p_evs_max_arr = np.zeros((2, M.n_scenarios, M.n_timesteps, M.n_evs), dtype='double')
    v_min_arr, v_max_arr = np.ones((2, M.n_scenarios, M.n_timesteps, M.n_nodes), dtype='double') * M.ref_voltage
    i_min_arr, i_max_arr = np.zeros((2, M.n_scenarios, M.n_timesteps, M.n_lines), dtype='double')
    soc_min_arr, soc_max_arr = np.zeros((2, M.n_scenarios, M.n_timesteps, M.n_evs), dtype='double')
    evs_utilities_coefs = np.zeros((M.n_scenarios, M.n_timesteps, M.n_evs))
    gens_utility_coefs = np.zeros((M.n_scenarios, M.n_timesteps, M.n_nodes))
    loads_utility_coefs = np.zeros((M.n_scenarios, M.n_timesteps, M.n_nodes))

    for sc_ind, sc in enumerate(scenarios):
        for t_ind in range(M.t_current_ind, M.t_end_ind + 1):
            t_hr = M.timesteps_hr[t_ind]
            # Bound nodal voltages and powers, compute generators utilities
            for node_ind, node in enumerate(surrogate_grid.nodes):
                if node.type == 'load':
                    active_evs_at_t_at_node = [ev for ev in sc.load_evs_presence[node_ind][t_ind] if ev.t_dep_hr > t_hr]
                    is_ev_present = len(active_evs_at_t_at_node) > 0
                    (p_min, p_max) = (node.p_min, node.p_max) if is_ev_present else (0, 0)
                    if is_ev_present:
                        loads_utility_coefs[sc_ind, t_ind, node_ind] = np.mean([ev.utility_coef
                                                                                for ev in active_evs_at_t_at_node])
                elif node.type == 'passive':
                    p_min, p_max = 0, 0
                elif node.type == 'gen':
                    p_min, p_max = node.p_min, node.p_max
                    gens_utility_coefs[sc_ind, t_ind, node_ind] = sc.power_price[t_ind]
                else:
                    raise ValueError('Unknown node type %s' % node.type)

                p_min_arr[sc_ind, t_ind, node_ind] = p_min
                p_max_arr[sc_ind, t_ind, node_ind] = p_max
                v_min_arr[sc_ind, t_ind, node_ind] = node.v_min
                v_max_arr[sc_ind, t_ind, node_ind] = node.v_max
            # Bound lines current
            for line_ind, line in enumerate(surrogate_grid.lines):
                i_max_arr[sc_ind, t_ind, line_ind] = line.i_max
                i_min_arr[sc_ind, t_ind, line_ind] = -line.i_max

        # Bound EV state-of-charge, compute EV utilities
        for ev_ind, ev in enumerate(sc.evs):
            t_arr_hr, t_dep_hr = ev.t_arr_hr, ev.t_dep_hr
            t_arr_ind = M.timesteps_hr.tolist().index(t_arr_hr)
            t_dep_ind = M.timesteps_hr.tolist().index(t_dep_hr)
            p_evs_max_arr[sc_ind, t_arr_ind: t_dep_ind, ev_ind] = M.p_max_loads_true / (M.norm_factor ** 2)
            soc_min_arr[sc_ind, t_arr_ind, ev_ind] = soc_max_arr[sc_ind, t_arr_ind, ev_ind] = ev.soc_arr
            soc_max_arr[sc_ind, t_arr_ind + 1: t_dep_ind + 1, ev_ind] = ev.soc_max
            soc_max_arr[sc_ind, :t_arr_ind, ev_ind] = soc_max_arr[sc_ind, t_dep_ind + 1:, ev_ind] = 0
            if ev.t_arr_hr <= M.t_current_hr <= ev.t_dep_hr:
                soc_min_arr[sc_ind, M.t_current_ind, ev_ind] = M.SOC_evs_current[ev_ind]
                soc_max_arr[sc_ind, M.t_current_ind, ev_ind] = M.SOC_evs_current[ev_ind]
            evs_utilities_coefs[sc_ind, t_arr_ind: t_dep_ind, ev_ind] = ev.utility_coef

    p_min_arr /= M.norm_factor ** 2
    p_max_arr /= M.norm_factor ** 2
    v_min_arr /= M.norm_factor
    v_max_arr /= M.norm_factor
    i_min_arr /= M.norm_factor
    i_max_arr /= M.norm_factor
    soc_min_arr /= M.norm_factor ** 2
    soc_max_arr /= M.norm_factor ** 2
    return (p_min_arr, p_max_arr, p_evs_min_arr, p_evs_max_arr, v_min_arr,
            v_max_arr, i_min_arr, i_max_arr, soc_min_arr, soc_max_arr,
            evs_utilities_coefs, gens_utility_coefs, loads_utility_coefs)
