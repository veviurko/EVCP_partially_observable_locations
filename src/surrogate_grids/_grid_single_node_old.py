from collections import defaultdict, deque
from src.grid.node import Node
from src.grid.line import Line
from src.grid.grid import Grid
import numpy as np


def compute_paths_from_ends(end_node, region, nodes_connectivity_dict, ):
    start_ind = end_node
    visited_nodes = {start_ind, }
    nodes_to_go = deque([start_ind])
    path = [line for ind, line in nodes_connectivity_dict[start_ind].items() if ind not in region]
    paths_from_ends = {start_ind: {start_ind: list(path)}}

    while len(nodes_to_go):
        current_ind = nodes_to_go.pop()
        children_inds = [i for i in nodes_connectivity_dict[current_ind] if i in region and i not in visited_nodes]
        for child_ind in children_inds:
            line = nodes_connectivity_dict[current_ind][child_ind]
            path_to_child = list(paths_from_ends[start_ind][current_ind] + [line])
            paths_from_ends[start_ind][child_ind] = path_to_child
            visited_nodes.add(child_ind)
        nodes_to_go.extend(children_inds)

    return paths_from_ends


def compute_avg_vals(end_node, region, nodes_connectivity_dict):
    path_from_ends = compute_paths_from_ends(end_node, region, nodes_connectivity_dict)

    avg_g_dict = {}
    avg_i_max_dict = {}

    for n_ind_from in path_from_ends:
        g_list = []
        i_max_list = []
        for n_ind_to, path in path_from_ends[n_ind_from].items():
            g_list.append(1 / (1e-10 + sum([1 / line.g for line in path])))
            i_max_list.append(np.min([line.i_max for line in path] + [1e99]) if len(path) else 0)

        avg_g_dict[n_ind_from] = np.mean(g_list)
        avg_i_max_dict[n_ind_from] = np.mean(i_max_list)
    return avg_g_dict, avg_i_max_dict


def create_grid_single_node(grid, ):
    grid_v_min = min([n.v_min for n in grid.nodes])
    grid_v_max = max([n.v_max for n in grid.nodes])

    # Create dictionary {node: region}
    node_to_region = {}
    for region in grid.loads_regions:
        for node_ind in region:
            node_to_region[node_ind] = region

    # Create dictionary {[i][j] : line_ij}
    nodes_connectivity_dict = defaultdict(dict)
    for line in grid.lines:
        node_from_ind = grid.nodes.index(line.node_from)
        node_to_ind = grid.nodes.index(line.node_to)
        nodes_connectivity_dict[node_from_ind][node_to_ind] = line
        nodes_connectivity_dict[node_to_ind][node_from_ind] = line

    # Create new grid
    lines_new = []
    nodes_new = []
    regions_new = []
    old_to_new_dict = {}
    for region_ind, region in enumerate(grid.loads_regions):
        if len(region) == 1:
            node_ind = region[0]
            nodes_new.append(grid.nodes[node_ind])
            regions_new.append([len(nodes_new) - 1])
            old_to_new_dict[node_ind] = len(nodes_new) - 1
            # Since the lines between big and small regions are created from 'perspective' of big ones,
            # Here we just connect small regions between each otehr
            connected_small_regions = [i for i in nodes_connectivity_dict[node_ind] if len(node_to_region[i]) == 1]
            for n_to in connected_small_regions:
                if nodes_connectivity_dict[node_ind][n_to] not in lines_new:
                    lines_new.append(nodes_connectivity_dict[node_ind][n_to])

        else:
            # Collect set of external nodes. For each line from such node to a load within region we create passive node
            external_nodes = set()
            for n_ind in region:
                for n_to_ind, line in nodes_connectivity_dict[n_ind].items():
                    if n_to_ind not in region or grid.nodes[n_to_ind].type == 'gen':
                        external_nodes.add(n_to_ind)
            end_nodes = [n_ind for n_ind in region if (grid.nodes[n_ind].type == 'gen') or
                         (len([i for i in nodes_connectivity_dict[n_ind].keys() if i not in region]) > 0)]
            total_p_max = sum([grid.nodes[n_ind].p_max for n_ind in region])
            aggregated_node = Node('Aggregated#%d'%region_ind, 'load', grid_v_min, grid_v_max,
                                   (grid_v_min + grid_v_max) / 2,  0, total_p_max)
            nodes_new.append(aggregated_node)
            for node_old_ind in region:
                old_to_new_dict[node_old_ind] = len(nodes_new) - 1
            region_extended = [len(nodes_new) - 1]
            for raw_ind, border_node_ind in enumerate(end_nodes):
                avg_g_dict, avg_i_max_dict = compute_avg_vals(border_node_ind, region, nodes_connectivity_dict)
                external_node_inds = [i for i in nodes_connectivity_dict[border_node_ind].keys() if not i in region]
                for external_node_ind in external_node_inds:
                    external_node = grid.nodes[external_node_ind]
                    external_node_region = [reg for reg in grid.loads_regions if external_node_ind in reg][0]
                    # assert len(external_node_region) == 1, 'Two >1 regions are connected'
                    lines_new.append(Line(external_node, aggregated_node,
                                          avg_i_max_dict[border_node_ind], avg_g_dict[border_node_ind]))
            regions_new.append(region_extended)
    regions_new_nodes = [[nodes_new[ind] for ind in reg] for reg in regions_new]
    # nodes_new = sorted(nodes_new, key=lambda x: grid.nodes.index(x) if x in grid.nodes else 9999)
    regions_new = [[nodes_new.index(node) for node in reg_n] for reg_n in regions_new_nodes]
    return Grid(grid.name + '_surrogate', nodes_new, lines_new, grid.ref_index, grid.ref_voltage,
                grid.con_groups, regions_new), old_to_new_dict
