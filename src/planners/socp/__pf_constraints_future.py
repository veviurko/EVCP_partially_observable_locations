from mosek.fusion import *
import numpy as np


def create_pf_constraints_future(M, surrogate_grid, scenarios,
                                 p_min_arr, p_max_arr, v_sq_min_arr, v_sq_max_arr, i_sq_min_arr, i_sq_max_arr):

    for sc_ind, sc in enumerate(scenarios):
        p_ij_list, p_ji_list = [], []
        v_i_list, v_j_list = [], []
        l_ij_list = []
        r_line_list = []
        P_nodes = M.variable('P_nodes_sc%d' % sc_ind, [M.n_ts_future, M.n_nodes],
                             Domain.inRange(p_min_arr[sc_ind, M.t_current_ind + 1:],
                                            p_max_arr[sc_ind, M.t_current_ind + 1:]))
        V_sq_nodes = M.variable('V_sq_nodes_sc%d' % sc_ind, [M.n_ts_future, M.n_nodes],
                                Domain.inRange(v_sq_min_arr[sc_ind, M.t_current_ind + 1:],
                                               v_sq_max_arr[sc_ind, M.t_current_ind + 1:]))
        P_lines = M.variable('P_lines_sc%d' % sc_ind, [M.n_ts_future, M.n_lines], Domain.unbounded())
        P_lines_neg = M.variable('P_lines_neg_sc%d' % sc_ind, [M.n_ts_future, M.n_lines], Domain.unbounded())
        I_sq_lines = M.variable('I_sq_lines_sc%d' % sc_ind, [M.n_ts_future, M.n_lines],
                                Domain.inRange(i_sq_min_arr[sc_ind, M.t_current_ind + 1:],
                                               i_sq_max_arr[sc_ind, M.t_current_ind + 1:]))
        I_sq_lines_neg = M.variable('I_sq_lines_neg_sc%d' % sc_ind, [M.n_ts_future, M.n_lines],
                                    Domain.inRange(i_sq_min_arr[sc_ind, M.t_current_ind + 1:],
                                                   i_sq_max_arr[sc_ind, M.t_current_ind + 1:]))

        for t_ind_true in range(M.t_current_ind + 1, M.t_end_ind + 1):
            t_ind = t_ind_true - M.t_current_ind - 1
            for i, n_i in enumerate(surrogate_grid.nodes):
                p_i = [P_nodes.index(t_ind, i)]
                for line in surrogate_grid.node_to_lines_dict[i]:
                    l_ind = surrogate_grid.lines.index(line)
                    n_j = line.node_from if n_i == line.node_to else line.node_to
                    j = surrogate_grid.nodes.index(n_j)
                    p_ij = P_lines_neg.index(t_ind, l_ind) if n_i == line.node_to else P_lines.index(t_ind, l_ind)
                    p_ji = P_lines.index(t_ind, l_ind) if n_i == line.node_to else P_lines_neg.index(t_ind, l_ind)
                    l_ij = I_sq_lines_neg.index(t_ind, l_ind) if n_i == line.node_to else I_sq_lines.index(t_ind, l_ind)
                    p_i.append(p_ij)
                    p_ij_list.append(p_ij)
                    p_ji_list.append(p_ji)
                    l_ij_list.append(l_ij)
                    v_i_list.append(V_sq_nodes.index(t_ind, i))
                    v_j_list.append(V_sq_nodes.index(t_ind, j))
                    r_line_list.append(1 / line.g)
                M.constraint(Expr.add(p_i), Domain.equalsTo(0.))
        if len(p_ij_list):
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
