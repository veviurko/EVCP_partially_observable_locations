from pyomo.environ import *


def create_soc_constraints(M, surrogate_grid, scenarios):
    # V2G is not allowed now, change the __create_bound to allow it
    # It is assumed that sc.index(ev) is equal for different scenario for evs that are already arrived !

    # Ensure that power to EVs in the node equals power in the node given by OPF
    M.evs_charge_balance_now_constraints = ConstraintList()
    for load_ind in surrogate_grid.load_inds:
        active_evs_at_t_at_node = [ev for ev in scenarios[0].load_evs_presence[load_ind][M.t_current_ind]
                                   if ev.t_dep_hr > M.t_current_hr]

        if len(active_evs_at_t_at_node):
            evs_total_charge = sum([M.P_evs_now[scenarios[0].evs.index(ev)] for ev in active_evs_at_t_at_node])
            M.evs_charge_balance_now_constraints.add(evs_total_charge == M.P_nodes_now[load_ind])

    # Do the same for future timesteps and constraint SOC dynamics
    M.evs_charge_balance_future_constraints = ConstraintList()
    M.soc_dynamics_constraints = ConstraintList()
    for sc_ind, sc in enumerate(scenarios):
        for t_ind_true in range(M.t_current_ind + 1, M.t_end_ind + 1):
            t_ind = t_ind_true - M.t_current_ind - 1
            t_hr_true = M.timesteps_hr[t_ind_true]
            for load_ind in surrogate_grid.load_inds:
                active_evs_at_t_at_node = [ev for ev in sc.load_evs_presence[load_ind][t_ind_true]
                                           if ev.t_dep_hr > t_hr_true]
                if len(active_evs_at_t_at_node):
                    evs_total_charge = sum([M.P_evs_sc[sc_ind, t_ind_true, scenarios[0].evs.index(ev)]
                                            for ev in active_evs_at_t_at_node])
                    M.evs_charge_balance_future_constraints.add(evs_total_charge ==
                                                                M.P_nodes_sc[sc_ind, t_ind_true, load_ind])

        # SOC dynamics

        # Current timestep update
        if M.t_current_ind < M.t_end_ind:
            evs_to_charge = [ev for ev in sc.evs if (ev.t_arr_hr <= M.t_current_hr) and (ev.t_dep_hr > M.t_current_hr)]
            for ev in evs_to_charge:
                ev_ind = sc.evs.index(ev)
                soc_old = M.SOC_evs_current[ev_ind] / (M.norm_factor ** 2)
                soc_new = M.P_evs_now[ev_ind] * M.dt + soc_old
                M.soc_dynamics_constraints.add(soc_new == M.SOC_evs_sc[sc_ind, M.t_current_ind + 1, ev_ind])

        # Future timesteps update
        for t_ind_true in range(M.t_current_ind + 1, M.t_end_ind + 1):
            t_ind = t_ind_true - M.t_current_ind - 1
            t_hr_true = M.timesteps_hr[t_ind_true]
            if t_ind_true < M.t_end_ind:
                evs_to_charge = [ev for ev in sc.evs if (ev.t_arr_hr <= t_hr_true) and (ev.t_dep_hr > t_hr_true)]
                for ev in evs_to_charge:
                    ev_ind = sc.evs.index(ev)
                    soc_old = M.SOC_evs_sc[(sc_ind, t_ind_true, ev_ind)]
                    soc_new = M.P_evs_sc[(sc_ind, t_ind_true, ev_ind)] * M.dt + soc_old
                    M.soc_dynamics_constraints.add(soc_new == M.SOC_evs_sc[sc_ind, t_ind_true + 1, ev_ind])
