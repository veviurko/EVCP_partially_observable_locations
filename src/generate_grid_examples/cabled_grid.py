from src.grid.grid import Node, Line, Grid
from collections import defaultdict
import random


def generate_cabled_grid(n_loads_per_cables_list, tree_cable_list,
                         gen_inside_list, gen_end_list, dgs_connections_list,
                         v_min=300, v_max=400,
                         gen_center_p_min=-50000, gen_end_p_min=-50000,
                         gen_inside_p_min=-50000, gen_dg_p_min=-5000,
                         load_p_max=10000, line_i_max=100, line_g=15, ):
    gen_p_max = 0
    load_p_min = 0
    gen_i_min = -1000
    gen_i_max = 0.1
    load_i_min = -.1
    load_i_max = 1000
    v_nominal = (v_min + v_max) / 2

    nodes, lines = [], []
    regions_list = []
    cable_to_load_inds = defaultdict(list)
    connected_node_inds = set()

    # Create central generator
    nodes.append(Node('Cent.Gen.', 'gen', v_min, v_max, v_nominal, gen_center_p_min, gen_p_max, gen_i_min, gen_i_max))
    regions_list.append([0])

    # Create cables
    dgs_created = 0
    for cable_ind, n_loads_cable in enumerate(n_loads_per_cables_list):
        add_gen_inside = gen_inside_list[cable_ind]
        add_gen_at_end = gen_end_list[cable_ind]
        is_tree_cable = tree_cable_list[cable_ind]
        node_from = nodes[0]
        loads_created_at_cable = 0
        for i in range(n_loads_cable):
            # Build loads in the cable by growing a tree
            load = Node('c%d_load%d' % (cable_ind, loads_created_at_cable), 'load', v_min, v_max, v_nominal,
                        load_p_min, load_p_max, load_i_min, load_i_max)
            nodes.append(load)
            loads_created_at_cable += 1
            connected_node_inds.add((nodes.index(node_from), len(nodes) - 1))
            connected_node_inds.add((len(nodes) - 1, nodes.index(node_from)))
            cable_to_load_inds[cable_ind].append(len(nodes) - 1)
            if is_tree_cable:
                node_from = nodes[random.choice(cable_to_load_inds[cable_ind])]
            else:
                node_from = nodes[-1]
        regions_list.append(list(cable_to_load_inds[cable_ind]))
        if add_gen_at_end:
            # Add generator at the end, if needed
            gen_end = Node('DG%d' % dgs_created, 'gen', v_min, v_max, v_nominal,
                           gen_end_p_min, gen_p_max, gen_i_min, gen_i_max)
            dgs_created += 1
            nodes.append(gen_end)
            connected_node_inds.add((len(nodes) - 2, len(nodes) - 1))
            connected_node_inds.add((len(nodes) - 1, len(nodes) - 2))
            regions_list.append([len(nodes) - 1])
        if add_gen_inside:
            # Add generator inside the cable, if needed
            gen_inside = Node('DG%d' % dgs_created, 'gen', v_min, v_max, v_nominal,
                              gen_inside_p_min, gen_p_max, gen_i_min, gen_i_max)
            dgs_created += 1
            nodes.append(gen_inside)
            node_from_ind = random.choice([n_ind for n_ind in cable_to_load_inds[cable_ind][1:-1]
                                           if nodes[n_ind].type != 'gen'])
            connected_node_inds.add((len(nodes) - 1, node_from_ind))
            connected_node_inds.add((node_from_ind, len(nodes) - 1))
            regions_list.append([len(nodes) - 1])

    for (cable_ind_from, rel_load_ind_from, cable_ind_to, rel_load_ind_to) in dgs_connections_list:
        gen_dg = Node('DG%d' % dgs_created, 'gen', v_min, v_max, v_nominal,
                      gen_dg_p_min, gen_p_max, gen_i_min, gen_i_max)
        dgs_created += 1
        nodes.append(gen_dg)
        regions_list.append([len(nodes) - 1])
        node_from_ind = cable_to_load_inds[cable_ind_from][rel_load_ind_from]
        node_to_ind = cable_to_load_inds[cable_ind_to][rel_load_ind_to]
        connected_node_inds.add((len(nodes) - 1, node_from_ind))
        connected_node_inds.add((node_from_ind, len(nodes) - 1))
        connected_node_inds.add((len(nodes) - 1, node_to_ind))
        connected_node_inds.add((node_to_ind, len(nodes) - 1))

    # Create lines
    dealt_with_pairs = set()
    for node_from_ind, node_to_ind in connected_node_inds:
        if (node_from_ind, node_to_ind) in dealt_with_pairs:
            continue
        node_from = nodes[node_from_ind]
        node_to = nodes[node_to_ind]
        lines.append(Line(node_from, node_to, line_i_max, line_g))
        dealt_with_pairs.add((node_from_ind, node_to_ind))
        dealt_with_pairs.add((node_to_ind, node_from_ind))

    name = ('CabledGrid%s_gens-end=%s_gens-inside=%s_dgs=%s_i-line-max=%d_p-gen-min=%d' %
            (n_loads_per_cables_list, gen_end_list,gen_inside_list, dgs_connections_list,
             line_i_max, gen_center_p_min))

    grid = Grid(name, nodes, lines, ref_index=0, ref_voltage=v_nominal, loads_regions=regions_list)
    return grid
