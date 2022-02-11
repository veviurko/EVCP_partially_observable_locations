from src.surrogate_grids._adjust_scenario_to_surrogate_grid import adjust_scenario
from src.simulation_tools.sample_ev_locations import create_scenario_evs_locations
from src.surrogate_grids.create_surrogate_grid import create_surrogate_grid
from src.simulation_tools.sample_future import sample_future
import numpy as np
import time


# assert observe_ev_locations in ['full', 'present', 'past', 'blind']
# assert future_model in ['known-future', 'sample', 'no-future']
# assert grid_transformation in [None, 'parallel', 'single-node']


def simulate(env, planner, max_steps=np.inf, normalize_opf=False, tee=False, ):
    env.reset()

    n_timesteps = env.timesteps_hr.shape[0]

    results_dict = {'planning time': np.empty(n_timesteps),
                    'execution time': np.empty(n_timesteps),
                    'V_nodes': np.empty((env.grid.n_nodes, n_timesteps)),
                    'V_nodes_plan': np.empty((env.grid.n_nodes, n_timesteps)),
                    'P_nodes': np.empty((env.grid.n_nodes, n_timesteps)),
                    'P_nodes_plan': np.empty((env.grid.n_nodes, n_timesteps)),
                    'I_nodes': np.empty((env.grid.n_nodes, n_timesteps)),
                    'I_nodes_plan': np.empty((env.grid.n_nodes, n_timesteps)),
                    'I_lines': np.empty((env.grid.n_lines, n_timesteps)),
                    'I_lines_plan': np.empty((env.grid.n_lines, n_timesteps)),
                    'SOC_evs': np.empty((len(env.scenario.evs), n_timesteps))}

    while not env.finished and env.t_ind < max_steps:
        if tee:
            print('Step ', env.t_ind)

        # 1. Sample scenario based on the access to future (planner.future_model)
        #    'known-future' -- the true scenario is used,
        #    'no-future' -- assume no new EVs arrive,
        #    'sample' -- sample scenario randomly
        sampled_scenarios = sample_future(env, planner)
        # 2. Create the surrogate grid and adjust scenario
        grid_to_use = env.grid.__copy__()
        if planner.unify_grid:
            grid_to_use.loads_regions = [[gen_ind] for gen_ind in grid_to_use.gen_inds]
            grid_to_use.loads_regions += [[pass_ind] for pass_ind in grid_to_use.passive_inds]
            grid_to_use.loads_regions += [[ind for ind in group if ind in grid_to_use.load_inds]
                                          for group in grid_to_use.con_groups]
        grid_surrogate, old_to_new_nodes_dict = create_surrogate_grid(grid_to_use, planner.grid_transformation,
                                                                      planner.use_weird_sur_grid)
        sampled_scenarios = [adjust_scenario(grid_surrogate, sc, old_to_new_nodes_dict) for sc in sampled_scenarios]
        # 2. Randomly sample EV locations within cables based on 'observe_ev_locations'
        sampled_scenarios_with_locations = []
        per_scenario_ev_maps = []
        for sc in sampled_scenarios:
            for _ in range(1):
                sc_loc, new_to_old_evs_now_dict = create_scenario_evs_locations(grid_to_use, sc, env.t_ind,
                                                                                planner.observe_ev_locations)
                sampled_scenarios_with_locations.append(sc_loc)
                per_scenario_ev_maps.append(new_to_old_evs_now_dict)
        sampled_scenarios = sampled_scenarios_with_locations
        # Step
        plan = planner.step(grid_to_use, grid_surrogate, sampled_scenarios, per_scenario_ev_maps,
                            env.t_ind, env.current_SOC)
        #for key in ['V_nodes', 'I_lines', 'P_nodes', 'I_nodes']:
        #    results_dict[key + '_plan'][:, env.t_ind] = plan[key][:len(results_dict[key + '_plan']), env.t_ind]
        time_start_execution = time.time()
        P_nodes_now = np.zeros(grid_to_use.n_nodes)
        for ev_ind, ev in enumerate(env.scenario.evs):
            if ev.t_arr_hr <= env.t_hr:
                p_ev = plan['P_evs_now'][ev_ind]
                node_ind = ev.load_ind
                P_nodes_now[node_ind] = p_ev
        utility_coefs = env.get_cost_coefs()
        p_lb, p_ub = np.zeros((2, grid_to_use.n_nodes,))
        p_lb[grid_to_use.gen_inds] = -1e10
        p_lb[grid_to_use.load_inds] = 0
        p_ub[grid_to_use.load_inds] = np.copy(P_nodes_now[grid_to_use.load_inds])
        p_ub[p_ub < p_lb] = p_lb[p_ub < p_lb]
        if -1e-6 <= p_ub[grid_to_use.load_inds].max() < 1e-6:
            p_ub[grid_to_use.load_inds] = np.zeros_like(p_ub[grid_to_use.load_inds])

        env.step(p_lb, p_ub, utility_coefs, normalize_opf=normalize_opf)
        execution_time = time.time() - time_start_execution
        #print('Plan:', np.array(p_ub, dtype='int'))
        #print('Exec:', np.array(env.P_nodes[:, env.t_ind - 1], dtype='int'))
        results_dict['planning time'][env.t_ind - 1] = plan['planning time']
        results_dict['execution time'][env.t_ind - 1] = execution_time
        results_dict['V_nodes'][:, env.t_ind - 1] = env.V_nodes[:, env.t_ind - 1]
        results_dict['P_nodes'][:, env.t_ind - 1] = env.P_nodes[:, env.t_ind - 1]
        results_dict['I_nodes'][:, env.t_ind - 1] = env.I_nodes[:, env.t_ind - 1]
        results_dict['I_lines'][:, env.t_ind - 1] = env.I_lines[:, env.t_ind - 1]
        results_dict['SOC_evs'][:, env.t_ind - 1] = env.SOC_evs[:, env.t_ind - 1]
    return results_dict
