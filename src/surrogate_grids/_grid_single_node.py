from collections import defaultdict, deque
from src.grid.node import Node
from src.grid.line import Line
from src.grid.grid import Grid
import numpy as np


def compute_paths_from_root(root_ind, nodes_connectivity_dict):
    visited_nodes = {root_ind}
    nodes_to_visit = deque([root_ind])
    paths_from_root = {root_ind: []}
    while len(nodes_to_visit):
        current_ind = nodes_to_visit.popleft()
        children_inds = [i for i in nodes_connectivity_dict[current_ind] if i not in visited_nodes]
        for child_ind in children_inds:
            line = nodes_connectivity_dict[current_ind][child_ind]
            path_to_child = list(paths_from_root[current_ind] + [line])
            paths_from_root[child_ind] = path_to_child
            visited_nodes.add(child_ind)
        nodes_to_visit.extend(children_inds)
    return paths_from_root


def create_grid_single_node(grid, use_max=False):
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

    new_nodes_connected_pair_inds = set()
    regions_connectivity_dict = defaultdict(lambda: defaultdict(list))
    for line in grid.lines:
        node_from_ind = grid.nodes.index(line.node_from)
        node_to_ind = grid.nodes.index(line.node_to)
        region_from_ind = [reg_ind for reg_ind, reg in enumerate(grid.loads_regions) if node_from_ind in reg][0]
        region_to_ind = [reg_ind for reg_ind, reg in enumerate(grid.loads_regions) if node_to_ind in reg][0]
        if region_from_ind != region_to_ind:
            regions_connectivity_dict[region_from_ind][region_to_ind].append(line)
            regions_connectivity_dict[region_to_ind][region_from_ind].append(line)
            new_nodes_connected_pair_inds.add((region_from_ind, region_to_ind))
            new_nodes_connected_pair_inds.add((region_to_ind, region_from_ind))

    paths_from_all_nodes = {root_ind: compute_paths_from_root(root_ind, nodes_connectivity_dict)
                            for root_ind in range(grid.n_nodes)}
    '''    for ind_from in paths_from_all_nodes:
        for ind_to in paths_from_all_nodes[ind_from]:
            if grid.nodes[ind_from].type == 'gen':
                print('node from', grid.nodes[ind_from], 'node to', grid.nodes[ind_to], 'len',
                      len(paths_from_all_nodes[ind_from][ind_to]))
                print('path', [(l.node_from, l.node_to) for l in paths_from_all_nodes[ind_from][ind_to]])'''
    lines_new = []
    nodes_new = []
    old_to_new_dict = {}
    for region_ind, region in enumerate(grid.loads_regions):
        if len(region) == 1:
            new_node = grid.nodes[region[0]]
        else:
            total_p_max = sum([grid.nodes[n_ind].p_max for n_ind in region])
            new_node = Node('Aggregated#%d' % region_ind, 'load', grid_v_min, grid_v_max,
                            (grid_v_min + grid_v_max) / 2, 0, total_p_max)
        nodes_new.append(new_node)
        for old_ind in region:
            old_to_new_dict[old_ind] = len(nodes_new) - 1

    already_connected_pairs = set()
    for node_i_ind, node_j_ind in new_nodes_connected_pair_inds:
        if (node_i_ind, node_j_ind) in already_connected_pairs:
            continue

        node_i = nodes_new[node_i_ind]
        node_j = nodes_new[node_j_ind]

        region_i = grid.loads_regions[node_i_ind]
        region_j = grid.loads_regions[node_j_ind]
        paths_between_regions = []
        for i_from in region_i:
            for j_to in region_j:
                path = paths_from_all_nodes[i_from][j_to]
                paths_between_regions.append(path)
        for j_from in region_j:
            for i_to in region_i:
                path = paths_from_all_nodes[j_from][i_to]
                paths_between_regions.append(path)

        per_path_g = []
        per_path_i_max = []
        for path in paths_between_regions:
            per_path_g.append(1 / np.sum([1 / l.g for l in path]))
            per_path_i_max.append(np.min([l.i_max for l in path]))
        # print('mean')
        if use_max:
            avg_g = np.max(per_path_g)
        else:
            avg_g = np.mean(per_path_g)
        # avg_g = np.mean(per_path_g)
        avg_i_max = np.mean(per_path_i_max)
        already_connected_pairs.add((node_i_ind, node_j_ind))
        already_connected_pairs.add((node_j_ind, node_i_ind))
        lines_new.append(Line(node_i, node_j, avg_i_max, avg_g))

    regions_new = [[i] for i in range(grid.n_nodes)]
    return (Grid(grid.name + '_single-node', nodes_new, lines_new, grid.ref_index, grid.ref_voltage,
                 regions_new), old_to_new_dict)
