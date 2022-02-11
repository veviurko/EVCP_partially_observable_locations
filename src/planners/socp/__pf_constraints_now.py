from mosek.fusion import *
import numpy as np


def create_pf_constraints_now(M, surrogate_grid,
                              p_min_arr, p_max_arr, v_sq_min_arr, v_sq_max_arr, i_sq_min_arr, i_sq_max_arr):
    # Create variables
    P_nodes = M.variable('P_nodes_now', [M.n_nodes],
                         Domain.inRange(p_min_arr[0, M.t_current_ind], p_max_arr[0, M.t_current_ind]))
    V_sq_nodes = M.variable('V_sq_nodes_now', [M.n_nodes],
                            Domain.inRange(v_sq_min_arr[0, M.t_current_ind], v_sq_max_arr[0, M.t_current_ind]))
    P_lines = M.variable('P_lines_now', [M.n_lines], Domain.unbounded())
    P_lines_neg = M.variable('P_lines_neg_now', [M.n_lines], Domain.unbounded())
    I_sq_lines = M.variable('I_sq_lines_now', [M.n_lines],
                            Domain.inRange(i_sq_min_arr[0, M.t_current_ind], i_sq_max_arr[0, M.t_current_ind]))
    I_sq_lines_neg = M.variable('I_sq_lines_neg_now', [M.n_lines],
                                Domain.inRange(i_sq_min_arr[0, M.t_current_ind], i_sq_max_arr[0, M.t_current_ind]))

    # Create constraints
    p_ij_list, p_ji_list = [],  []
    v_i_list, v_j_list = [], []
    l_ij_list = []
    r_line_list = []

    for node_ind, node in enumerate(surrogate_grid.nodes):
        p_i = [P_nodes.index(node_ind)]
        for line in surrogate_grid.node_to_lines_dict[node_ind]:
            l_ind = surrogate_grid.lines.index(line)
            node_to = line.node_from if node == line.node_to else line.node_to
            node_to_ind = surrogate_grid.nodes.index(node_to)
            p_ij = (P_lines_neg.index(l_ind) if node == line.node_to else P_lines.index(l_ind))
            p_ji = (P_lines.index(l_ind) if node == line.node_to else P_lines_neg.index(l_ind))
            l_ij = (I_sq_lines_neg.index(l_ind) if node == line.node_to else I_sq_lines.index(l_ind))
            p_i.append(p_ij)
            p_ij_list.append(p_ij)
            p_ji_list.append(p_ji)
            l_ij_list.append(l_ij)
            v_i_list.append(V_sq_nodes.index(node_ind))
            v_j_list.append(V_sq_nodes.index(node_to_ind))
            r_line_list.append(1 / line.g)
        M.constraint(Expr.add(p_i), Domain.equalsTo(0.))

    p_ij = Expr.vstack(p_ij_list)
    p_ji = Expr.vstack(p_ji_list)
    l_ij = Expr.vstack(l_ij_list)
    v_i = Expr.vstack(v_i_list)
    v_j = Expr.vstack(v_j_list)
    v_diff = Expr.sub(v_i, v_j)
    p_diff = Expr.sub(Expr.vstack(p_ij_list), Expr.vstack(p_ji_list))
    z = Expr.hstack(Expr.mul(l_ij, 1 / 2), v_i, p_ij)
    r = np.array(r_line_list)
    M.constraint(Expr.add([p_ij, p_ji, Expr.mulElm(Expr.neg(l_ij), r)]), Domain.equalsTo(0.))
    M.constraint(Expr.sub(v_diff, Expr.mulElm(p_diff, r)), Domain.equalsTo(0.))
    M.constraint(z, Domain.inRotatedQCone(z.getDim(0), 3))
