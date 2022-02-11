from mosek.fusion import *


def create_soc_constraints(M, surrogate_grid, scenarios, p_evs_min_arr, p_evs_max_arr, soc_min_arr, soc_max_arr):
    # V2G is not allowed now, change the __create_bound to allow it
    # It is assumed that sc.index(ev) is equal for different scenario for evs that are already arrived !
    p_to_evs_list, p_at_node_list = [], []
    soc_goals_list, soc_vars_list = [], []

    # Ensure that power to evs in the node equals power in the node given by OPF
    P_evs_now = M.variable('P_evs_now', [M.n_evs],
                           Domain.inRange(p_evs_min_arr[0, M.t_current_ind], p_evs_max_arr[0, M.t_current_ind]))

    for load_ind in surrogate_grid.load_inds:
        active_evs_at_t_at_node = [ev for ev in scenarios[0].load_evs_presence[load_ind][M.t_current_ind]
                                   if ev.t_dep_hr > M.t_current_hr]
        if len(active_evs_at_t_at_node):
            p_to_evs_list.append(Expr.add([P_evs_now.index(scenarios[0].evs.index(ev))
                                           for ev in active_evs_at_t_at_node]))
            p_at_node_list.append(M.getVariable('P_nodes_now').index(load_ind))

    for sc_ind, sc in enumerate(scenarios):
        P_evs_sc = M.variable('P_evs_sc%d' % sc_ind, [M.n_ts_future, M.n_evs],
                              Domain.inRange(p_evs_min_arr[sc_ind, M.t_current_ind + 1:],
                                             p_evs_max_arr[sc_ind, M.t_current_ind + 1:]))
        for t_ind_true in range(M.t_current_ind + 1, M.t_end_ind + 1):
            t_ind = t_ind_true - M.t_current_ind - 1
            t_hr_true = M.timesteps_hr[t_ind_true]
            for load_ind in surrogate_grid.load_inds:
                active_evs_at_t_at_node = [ev for ev in sc.load_evs_presence[load_ind][t_ind_true]
                                           if ev.t_dep_hr > t_hr_true]
                if len(active_evs_at_t_at_node):
                    p_to_evs_list.append(Expr.add([P_evs_sc.index(t_ind, sc.evs.index(ev))
                                                   for ev in active_evs_at_t_at_node]))
                    p_at_node_list.append(M.getVariable('P_nodes_sc%d' % sc_ind).index(t_ind, load_ind))

        # Future SOC dynamics
        SOC_evs = M.variable('SOC_evs_sc%d' % sc_ind, [M.n_ts_future, M.n_evs],
                             Domain.inRange(soc_min_arr[sc_ind, M.t_current_ind + 1:],
                                            soc_max_arr[sc_ind, M.t_current_ind + 1:]))
        # Current timestep update
        #print('Current t', M.t_current_ind, M.t_current_hr)
        #print('SOC NOW', M.SOC_evs_current)

        if M.t_current_ind < M.t_end_ind:
            evs_to_charge = [ev for ev in sc.evs if (ev.t_arr_hr <= M.t_current_hr) and (ev.t_dep_hr > M.t_current_hr)]
            for ev in evs_to_charge:
                ev_ind = sc.evs.index(ev)
                soc_old = M.SOC_evs_current[ev_ind] / (M.norm_factor ** 2)
                soc_new_goal = Expr.add(Expr.mul(P_evs_now.index(ev_ind), M.dt), soc_old)
                soc_new_var = SOC_evs.index(0, ev_ind)
                soc_goals_list.append(soc_new_goal)
                #print('soc_old', soc_old)
                soc_vars_list.append(soc_new_var)
        # Future timesteps update
        for t_ind_true in range(M.t_current_ind + 1, M.t_end_ind + 1):
            t_ind = t_ind_true - M.t_current_ind - 1
            t_hr_true = M.timesteps_hr[t_ind_true]
            if t_ind_true < M.t_end_ind:
                evs_to_charge = [ev for ev in sc.evs if (ev.t_arr_hr <= t_hr_true) and (ev.t_dep_hr > t_hr_true)]
                for ev in evs_to_charge:
                    ev_ind = sc.evs.index(ev)
                    soc_old = SOC_evs.index(t_ind, ev_ind)
                    soc_new_goal = Expr.add(Expr.mul(P_evs_sc.index(t_ind, ev_ind), M.dt), soc_old)
                    soc_new_var = SOC_evs.index(t_ind + 1, ev_ind)
                    soc_goals_list.append(soc_new_goal)
                    soc_vars_list.append(soc_new_var)
    if len(soc_goals_list):
        p_to_evs = Expr.vstack(p_to_evs_list)
        p_at_node = Expr.vstack(p_at_node_list)
        soc_goals = Expr.vstack(soc_goals_list)
        soc_vars = Expr.vstack(soc_vars_list)
        M.constraint(Expr.sub(p_to_evs, p_at_node), Domain.equalsTo(0.))
        M.constraint(Expr.sub(soc_goals, soc_vars), Domain.equalsTo(0.))
