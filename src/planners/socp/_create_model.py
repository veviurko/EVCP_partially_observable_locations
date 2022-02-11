from src.planners.socp.__pf_constraints_future import create_pf_constraints_future
from src.planners.socp.__pf_constraints_now import create_pf_constraints_now
from src.planners.socp.__soc_constraints import create_soc_constraints
from src.planners.socp.__create_bounds import create_bounds
from src.scenario.scenario import Scenario
from src.grid.grid import Grid
from mosek.fusion import *
from typing import List
import numpy as np


def create_model(true_grid: Grid,
                 surrogate_grid: Grid,
                 scenarios: List[Scenario],
                 t_current_ind: int,
                 SOC_evs_current: np.ndarray,
                 obj_factor: float = 1,
                 norm_factor: float = 1,
                 **solver_options):

    M = Model('SOCP_planner')
    M.timesteps_hr = scenarios[0].timesteps_hr
    M.n_timesteps = len(M.timesteps_hr)
    M.t_current_ind = t_current_ind
    M.t_current_hr = M.timesteps_hr[t_current_ind]
    M.t_end_ind = scenarios[0].t_end_ind
    M.n_ts = len(M.timesteps_hr)
    M.n_ts_future = M.n_timesteps - 1 - M.t_current_ind
    M.dt = scenarios[0].ptu_size_hr

    M.p_max_loads_true = np.mean([n.p_max for n in true_grid.loads])
    M.n_nodes = surrogate_grid.n_nodes
    M.n_lines = surrogate_grid.n_lines
    M.n_scenarios = len(scenarios)
    M.n_evs = max([len(sc.evs) for sc in scenarios])

    M.ref_voltage = true_grid.ref_voltage
    M.norm_factor = norm_factor
    M.obj_factor = obj_factor
    M.SOC_evs_current = SOC_evs_current

    (p_min_arr, p_max_arr, p_evs_min_arr, p_evs_max_arr,  v_sq_min_arr,
     v_sq_max_arr, i_sq_min_arr, i_sq_max_arr, soc_min_arr, soc_max_arr,
     evs_utilities_coefs, gens_utility_coefs, loads_utility_coefs) = create_bounds(M, surrogate_grid, scenarios)

    # Create grid state variable and PF constraints for both current and future timesteps, then create SOC constraints
    create_pf_constraints_now(M, surrogate_grid, p_min_arr, p_max_arr, v_sq_min_arr,
                              v_sq_max_arr, i_sq_min_arr, i_sq_max_arr)
    #print(np.sqrt(i_sq_min_arr * norm_factor ** 2),
    #      np.sqrt(i_sq_max_arr * norm_factor ** 2),)
    create_pf_constraints_future(M, surrogate_grid, scenarios, p_min_arr, p_max_arr, v_sq_min_arr,
                                 v_sq_max_arr, i_sq_min_arr, i_sq_max_arr)

    create_soc_constraints(M, surrogate_grid, scenarios, p_evs_min_arr, p_evs_max_arr, soc_min_arr, soc_max_arr)

    # Create objectives

    ev_utilities_now = evs_utilities_coefs[0, M.t_current_ind]
    gens_utilities_now = gens_utility_coefs[0, M.t_current_ind]
    current_objective = Expr.mul(Expr.add(Expr.dot(M.getVariable('P_evs_now'), ev_utilities_now),
                                          Expr.dot(M.getVariable('P_nodes_now'), gens_utilities_now)),
                                 M.dt * obj_factor)
    per_sc_future_objective = []
    for sc_ind, sc in enumerate(scenarios):
        ev_utilities_future = evs_utilities_coefs[sc_ind, M.t_current_ind + 1:]
        gens_utilities_future = gens_utility_coefs[sc_ind, M.t_current_ind + 1:]
        utility_to_evs = Expr.dot(M.getVariable('P_evs_sc%d' % sc_ind), ev_utilities_future)
        power_cost = Expr.dot(M.getVariable('P_nodes_sc%d' % sc_ind), gens_utilities_future)
        sc_objective = Expr.mul(Expr.add(utility_to_evs, power_cost), M.dt * obj_factor)
        per_sc_future_objective.append(sc_objective)
    future_objective = Expr.mul(Expr.add(per_sc_future_objective), 1 / M.n_scenarios)
    total_objective = Expr.add(current_objective, future_objective)
    M.objective(ObjectiveSense.Maximize, total_objective)

    for key, val in solver_options.items():
        M.setSolverParam(key, val)
    return M
