from src.planners.exact.__pf_constraints_future import create_pf_constraints_future
from src.planners.exact.__pf_constraints_now import create_pf_constraints_now
from src.planners.exact.__soc_constraints import create_soc_constraints
from src.planners.exact.__create_variables import create_variables
from src.planners.exact.__create_bounds import create_bounds
from src.scenario.scenario import Scenario
from src.grid.grid import Grid
from pyomo.environ import *
from typing import List
import numpy as np


def create_model(opf_method,
                 true_grid: Grid,
                 surrogate_grid: Grid,
                 scenarios: List[Scenario],
                 t_current_ind: int,
                 SOC_evs_current: np.ndarray,
                 obj_factor: float = 1,
                 norm_factor: float = 1):

    M = ConcreteModel()
    M.timesteps_hr = scenarios[0].timesteps_hr
    M.n_timesteps = len(M.timesteps_hr)
    M.t_current_ind = t_current_ind
    M.t_current_hr = M.timesteps_hr[t_current_ind]
    M.t_end_ind = scenarios[0].t_end_ind
    M.n_ts = len(M.timesteps_hr)
    M.n_ts_future = M.n_timesteps - 1 - M.t_current_ind
    M.dt = scenarios[0].ptu_size_hr
    M.timesteps_future = Set(initialize=range(M.t_current_ind + 1, M.t_end_ind + 1))

    M.p_max_loads_true = np.mean([n.p_max for n in true_grid.loads])
    M.n_nodes = surrogate_grid.n_nodes
    M.nodes = Set(initialize=range(0, M.n_nodes))
    M.n_lines = surrogate_grid.n_lines
    M.lines = Set(initialize=range(0, M.n_lines))
    M.n_scenarios = len(scenarios)
    M.scenarios = Set(initialize=range(0, M.n_scenarios))
    M.n_evs = max([len(sc.evs) for sc in scenarios])
    M.evs = Set(initialize=range(0, M.n_evs))

    M.ref_voltage = true_grid.ref_voltage
    M.norm_factor = norm_factor
    M.obj_factor = obj_factor
    M.SOC_evs_current = SOC_evs_current

    # Create bounds and variables
    (p_min_arr, p_max_arr, p_evs_min_arr, p_evs_max_arr, v_min_arr, v_max_arr, i_min_arr, i_max_arr, soc_min_arr,
     soc_max_arr, evs_utilities_coefs, gens_utility_coefs, loads_utility_coefs) = create_bounds(M, surrogate_grid,
                                                                                                scenarios)
    create_variables(M, p_min_arr, p_max_arr, p_evs_min_arr, p_evs_max_arr, v_min_arr, v_max_arr, i_min_arr, i_max_arr,
                     soc_min_arr, soc_max_arr)

    # Create PF constraints
    create_pf_constraints_now(M, surrogate_grid, opf_method)
    create_pf_constraints_future(M, surrogate_grid, opf_method)

    # Create SOC constraints
    create_soc_constraints(M, surrogate_grid, scenarios)

    # Create objective
    utility_to_evs_now = sum([M.P_evs_now[ev_ind] * M.dt * evs_utilities_coefs[0, M.t_current_ind, ev_ind]
                              for ev_ind in M.evs])
    power_cost_now = sum([M.P_nodes_now[gen_ind] * M.dt * gens_utility_coefs[0, M.t_current_ind, gen_ind]
                          for gen_ind in surrogate_grid.gen_inds])
    current_objective = (utility_to_evs_now + power_cost_now) * obj_factor

    per_sc_future_objective = []
    for sc_ind, sc in enumerate(scenarios):
        utility_to_evs_future_sc = sum([M.P_evs_sc[sc_ind, t_ind, ev_ind] * M.dt * evs_utilities_coefs[sc_ind, t_ind, ev_ind]
                                        for t_ind in M.timesteps_future for ev_ind in M.evs])
        power_cost_future_sc = sum([M.P_nodes_sc[sc_ind, t_ind, gen_ind] * M.dt * gens_utility_coefs[sc_ind, t_ind, gen_ind]
                                    for t_ind in M.timesteps_future for gen_ind in surrogate_grid.gen_inds])
        sc_objective = (utility_to_evs_future_sc + power_cost_future_sc) * obj_factor
        per_sc_future_objective.append(sc_objective)
    future_objective = np.mean(per_sc_future_objective)
    total_objective = current_objective + future_objective
    M.power_consumed = Objective(sense=maximize, expr=total_objective)
    return M
