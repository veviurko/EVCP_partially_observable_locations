from src.surrogate_grids._grid_parallel_nodes import create_grid_parallel_nodes
from src.surrogate_grids._grid_single_node import create_grid_single_node
#from src.simulation_tools._grid_single_node_old import create_grid_single_node


SUPPORTED_TRANSFORMATIONS = [None, 'parallel', 'single-node']


def create_surrogate_grid(grid, grid_transformation, use_weird_sur_grid=False):
    assert grid_transformation in SUPPORTED_TRANSFORMATIONS, ('Unsupported grid transformation %s!'
                                                              '\n Use on from %s.' % (grid_transformation,
                                                                                      SUPPORTED_TRANSFORMATIONS))
    if grid_transformation is None:
        grid_surrogate = grid
        old_to_new_nodes_dict = {node_ind: node_ind for node_ind in range(grid.n_nodes)}
    elif grid_transformation == 'parallel':
        grid_surrogate, old_to_new_nodes_dict = create_grid_parallel_nodes(grid, use_weird_sur_grid)
    elif grid_transformation == 'single-node':
        grid_surrogate, old_to_new_nodes_dict = create_grid_single_node(grid, use_weird_sur_grid)
    else:
        raise NotImplementedError('grid_transformation=%s is not implemented' % grid_transformation)
    #print(old_to_new_nodes_dict)
    #new_evs_list = []
    #for ev_ind, ev in enumerate(scenario.evs):
    #    new_node_ind = old_to_new_nodes_dict[ev.load_ind]
    #    ev_new = EV(new_node_ind, ev.soc_arr, ev.soc_goal, ev.soc_max, ev.t_arr_hr, ev.t_dep_hr, ev.utility_coef)
    #    new_evs_list.append(ev_new)
    #scenario_surrogate = Scenario(grid_surrogate.load_inds, scenario.timesteps_hr, new_evs_list, scenario.power_price)

    return grid_surrogate, old_to_new_nodes_dict
