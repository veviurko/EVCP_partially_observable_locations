from src.scenario.scenario import Scenario
from src.grid.electrical_vehicle import EV
import numpy as np


def create_scenario_evs_locations(grid, scenario, t_current_ind, observe_ev_locations='full'):
    t_current_hr = scenario.timesteps_hr[t_current_ind]
    if observe_ev_locations == 'full':
        new_to_old_evs_now_dict = {ev_ind: ev_ind for ev_ind in range(len(scenario.evs))
                                   if scenario.evs[ev_ind].t_arr_hr <= t_current_hr <= scenario.evs[ev_ind].t_dep_hr}
        return scenario, new_to_old_evs_now_dict

    timesteps_hr = scenario.timesteps_hr
    new_evs_list = []
    load_ind_business = {load_ind: np.zeros(len(timesteps_hr)) for load_ind in grid.load_inds}
    new_to_old_evs_now_dict = {}
    for t_ind, t_hr in enumerate(timesteps_hr):
        evs_arrive_at_t = scenario.t_ind_arrivals[t_ind]
        know_true_load_ind = ((observe_ev_locations == 'past' and t_ind < t_current_ind) or
                              (observe_ev_locations == 'present' and t_ind <= t_current_ind)
                              or observe_ev_locations == 'full')
        for ev in evs_arrive_at_t:
            old_ev_ind = scenario.evs.index(ev)
            if know_true_load_ind:
                new_load_ind = ev.load_ind
            else:
                region = [reg for reg in grid.loads_regions if ev.load_ind in reg][0]
                region_free_loads = [load_ind for load_ind in region if load_ind_business[load_ind][t_ind] == 0]
                new_load_ind = np.random.choice(region_free_loads)

            new_ev = EV(new_load_ind, ev.soc_arr, ev.soc_goal, ev.soc_max, ev.t_arr_hr, ev.t_dep_hr, ev.utility_coef)
            new_ev_ind = len(new_evs_list)
            new_evs_list.append(new_ev)
            t_arr_ind = int(ev.t_arr_hr // scenario.ptu_size_hr)
            t_dep_ind = int(ev.t_dep_hr // scenario.ptu_size_hr)
            if t_ind <= t_current_ind:
                new_to_old_evs_now_dict[new_ev_ind] = old_ev_ind
            load_ind_business[new_load_ind][t_arr_ind: t_dep_ind] = 1

    scenario_surrogate = Scenario(grid.load_inds, timesteps_hr, new_evs_list, scenario.power_price)
    return scenario_surrogate, new_to_old_evs_now_dict


