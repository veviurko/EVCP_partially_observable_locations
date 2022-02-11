from src.grid.grid import Node, Line, Grid
import numpy as np


def generate_IEEE16(meshed, grid_connected, v_min=300, v_max=400,
                    gen_p_min=-5000, gen_p_max=0,
                    load_p_max=20000, load_p_min=0,
                    line_i_max=100, line_g=30):
    gen_i_min = -1000
    gen_i_max = 0.1
    load_i_min = -.1
    load_i_max = 1000
    feeder_p_max = .1
    if grid_connected:
        feeder_p_min = -load_p_max * 20
    else:
        feeder_p_min = -.1
    v_nominal = (v_min + v_max) / 2

    load_inds = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    dg_inds = [16, 17, 18, 19, 20, 21]
    loads_regions = [[0], [1], [2]] + [[3, 4, 5, 6], [7, 8, 9, 10, 11], [12, 13, 14, 15]] + [[i] for i in dg_inds]
    connected_nodes = [(0, 3), (3, 4), (3, 5), (5, 6), (1, 7), (7, 8), (7, 9), (8, 10), (8, 11),
                       (2, 12), (12, 13), (12, 14), (14, 15), (5, 16), (4, 17), (8, 18), (9, 19), (11, 20),
                       (14, 21)]
    groups = None if meshed else [(0, 3, 4, 5, 6, 16, 17), (1, 7, 8, 9, 10, 11, 18, 19, 20),
                                  (2, 12, 13, 14, 15, 21)]
    if meshed:
        connected_nodes.extend([(4, 10), (9, 13), (6, 15)])

    n_loads = len(load_inds)
    n_gens = len(dg_inds) + 3
    n_nodes = n_loads + n_gens
    nodes = [_ for _ in range(n_nodes)]
    lines = []

    # Create feeder gens
    nodes[0] = Node('Feeder A', 'gen', v_min, v_max, v_nominal, feeder_p_min, feeder_p_max, gen_i_min, gen_i_max)
    nodes[1] = Node('Feeder B', 'gen', v_min, v_max, v_nominal, feeder_p_min, feeder_p_max, gen_i_min, gen_i_max)
    nodes[2] = Node('Feeder C', 'gen', v_min, v_max, v_nominal, feeder_p_min, feeder_p_max, gen_i_min, gen_i_max)

    # Create loads
    for load_node_ind in load_inds:
        nodes[load_node_ind] = Node('load_%d' % (load_node_ind + 1), 'load', v_min, v_max, v_nominal,
                                    load_p_min, load_p_max, load_i_min, load_i_max)
    # Create DGs
    for dg_node_ind in dg_inds:
        nodes[dg_node_ind] = Node('DG_%d' % (dg_node_ind + 1), 'gen', v_min, v_max, v_nominal,
                                  gen_p_min, gen_p_max, gen_i_min, gen_i_max)

    # Create lines
    for node_from_ind, node_to_ind in connected_nodes:
        node_from = nodes[node_from_ind]
        node_to = nodes[node_to_ind]
        lines.append(Line(node_from, node_to, line_i_max, line_g))

    # Grid
    meshed_str = 'meshed' if meshed else 'radial'
    external_grid_str = 'con' if grid_connected else 'disc'
    name = 'IEEE16%s_%s_g=%d_i-line-max=%d_p-gen-min=%d' % (meshed_str, external_grid_str,
                                                            line_g, line_i_max, gen_p_min)
    grid = Grid(name, nodes, lines, ref_index=0, ref_voltage=v_nominal, loads_regions=loads_regions)
    return grid
