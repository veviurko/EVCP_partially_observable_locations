from src.scenario.scenario import Scenario
from src.grid.electrical_vehicle import EV


def adjust_scenario(grid_surrogate, scenario, old_to_new_nodes_dict):
    new_evs_list = []
    for ev in scenario.evs:
        load_ind_old = ev.load_ind
        load_ind_new = old_to_new_nodes_dict[load_ind_old]
        ev_new = EV(load_ind_new, ev.soc_arr, ev.soc_goal, ev.soc_max, ev.t_arr_hr, ev.t_dep_hr, ev.utility_coef)
        new_evs_list.append(ev_new)
    #print('surrogatel oad inds', grid_surrogate.load_inds)
    #print('inds of evs', [ev.load_ind for ev in new_evs_list])
    return Scenario(grid_surrogate.load_inds, scenario.timesteps_hr, new_evs_list, scenario.power_price)
