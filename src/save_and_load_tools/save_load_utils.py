import pandas as pd
import numpy as np
import pickle
import os


# This file contains various functions for loading and saving  grids, scenarios and simulation results

def save_grid(grid, experiment_name, grid_name, path_to_experiments):
    if grid_name is not None:
        with open(path_to_experiments + '%s/%s/grid.pickle' % (experiment_name, grid_name), 'wb') as f:
            pickle.dump(grid, f)
    else:
        with open(path_to_experiments + '/%s/grid.pickle' % experiment_name, 'wb') as f:
            pickle.dump(grid, f)


def load_grid(experiment_name, grid_name, path_to_experiments):
    if grid_name is not None:
        with open(path_to_experiments + '/%s/%s/grid.pickle' % (experiment_name, grid_name), 'rb') as f:
            grid = pickle.load(f)
    else:
        with open(path_to_experiments + '/%s/grid.pickle' % (experiment_name), 'rb') as f:
            grid = pickle.load(f)
    return grid


def save_scenarios(scenarios, scenario_generator, experiment_name, grid_name, path_to_experiments):
    ptu_str = 't=%d' % scenario_generator.ptu_size_minutes
    with open(path_to_experiments + '/%s/%s/scenarios_%s.pickle' %
              (experiment_name, grid_name, ptu_str), 'wb') as f:
        pickle.dump(scenarios, f)
    with open(path_to_experiments + '/%s/%s/scenario_generator_%s.pickle' %
              (experiment_name, grid_name, ptu_str), 'wb') as f:
        pickle.dump(scenario_generator, f)


def load_scenarios(experiment_name, grid_name, path_to_experiments, ptu_int=60):
    ptu_str = 't=%d' % ptu_int
    with open(path_to_experiments + '/%s/%s/scenarios_%s.pickle' %
              (experiment_name, grid_name, ptu_str), 'rb') as f:
        scenarios = pickle.load(f)
    with open(path_to_experiments + '/%s/%s/scenario_generator_%s.pickle' %
              (experiment_name, grid_name, ptu_str), 'rb') as f:
        scenario_generator = pickle.load(f)
    return scenarios, scenario_generator


def save_simulations(experiment_name, grid_name, path_to_experiments, p_nodes, v_nodes, i_nodes, i_lines,
                     file_name='simulations.csv'):
    all_data = np.concatenate([p_nodes, v_nodes, i_nodes, i_lines], 1)
    n_nodes = p_nodes.shape[1]
    n_lines = i_lines.shape[1]
    columns = []
    columns.extend(['P_node_%d' % i for i in range(n_nodes)])
    columns.extend(['V_node_%d' % i for i in range(n_nodes)])
    columns.extend(['I_node_%d' % i for i in range(n_nodes)])
    columns.extend(['I_line_%d' % i for i in range(n_lines)])
    df = pd.DataFrame(all_data, columns=columns)
    df.to_csv(path_to_experiments + '/%s/%s/opf_data/%s' % (experiment_name, grid_name, file_name), index=False)


def load_simulations(experiment_name, grid_name, path_to_experiments,
                     file_name='simulations.csv'):
    simulations = pd.read_csv(path_to_experiments + '/%s/%s/opf_data/%s' % (experiment_name, grid_name, file_name))
    p_nodes_cols = [c for c in simulations.columns if 'P_node' in c]
    v_nodes_cols = [c for c in simulations.columns if 'V_node' in c]
    i_nodes_cols = [c for c in simulations.columns if 'I_node' in c]
    i_lines_cols = [c for c in simulations.columns if 'I_line' in c]

    p_nodes = simulations[p_nodes_cols].values
    v_nodes = simulations[v_nodes_cols].values
    i_nodes = simulations[i_nodes_cols].values
    i_lines = simulations[i_lines_cols].values

    return p_nodes, v_nodes, i_nodes, i_lines


def save_regressors_dict(regressors_dict, experiment_name, grid_name, path_to_experiments, dict_name):
    with open(experiment_name + '/%s/%s/opf_data/%s.pickle' % (experiment_name, grid_name, dict_name),
              'wb') as f:
        pickle.dump(regressors_dict, f)


def load_regressors_dict(experiment_name, grid_name, path_to_experiments, dict_name):
    with open(path_to_experiments + '/%s/%s/opf_data/%s.pickle' % (experiment_name, grid_name, dict_name), 'rb') as f:
        regressors_dict = pickle.load(f)
    return regressors_dict


def load_results_dict(planner_name,  experiment_name, grid_name, path_to_experiments):
    path_to_results_dict = path_to_experiments + '/%s/%s/results/' % (experiment_name, grid_name)
    results_dict_name = planner_name + '_results.pickle'
    if os.path.isdir(path_to_results_dict) and results_dict_name in os.listdir(path_to_results_dict):
        with open(path_to_results_dict + results_dict_name, 'rb') as f:
            results_dict = pickle.load(f)
        print('Loaded results dict')
    else:
        results_dict = dict()
        print('Created empty results dict')

    return results_dict


def save_results_dict(results_dict, planner_name, experiment_name, grid_name, path_to_experiments):
    path_to_results_dict = path_to_experiments + '/%s/%s/results/' % (experiment_name, grid_name)
    if not os.path.isdir(path_to_results_dict):
        os.makedirs(path_to_results_dict)
    results_dict_name = planner_name + '_results.pickle'
    with open(path_to_results_dict + results_dict_name, 'wb') as f:
        pickle.dump(results_dict, f)
