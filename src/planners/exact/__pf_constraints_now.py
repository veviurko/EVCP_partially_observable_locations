from pyomo.environ import *


def create_pf_constraints_now(M, surrogate_grid, opf_method):
    assert opf_method in ['exact', 'lossless'], 'Unknown opf_method %s' % opf_method

    # Ohm's Law
    M.ohm_law_now_constraints = ConstraintList()
    for line_ind, line in enumerate(surrogate_grid.lines):
        node_from_ind = surrogate_grid.nodes.index(line.node_from)
        node_to_ind = surrogate_grid.nodes.index(line.node_to)
        line_i = line.g * (M.V_nodes_now[node_from_ind] - M.V_nodes_now[node_to_ind])
        M.ohm_law_now_constraints.add(M.I_lines_now[line_ind] == line_i)

    # Power flow
    M.power_balance_now_constraints = ConstraintList()
    for n1_ind, n1 in enumerate(surrogate_grid.nodes):
        v_node = M.V_nodes_now[n1_ind] if opf_method == 'exact' else M.ref_voltage
        p_node = -v_node * sum([surrogate_grid.Y[n1_ind, n2_ind] * M.V_nodes_now[n2_ind]
                                for n2_ind in range(surrogate_grid.n_nodes)])
        M.power_balance_now_constraints.add(M.P_nodes_now[n1_ind] == p_node)


