from src.grid.grid import Grid
from pyomo.environ import *


def create_model(grid: Grid, normalize: bool = False):
    """
     Create a Pyomo model for the OPF problem.
     grid -- Grid object specifying the topology and parameters of the grid.
             Load power bounds are specified in the grid.loads[i].p_max
     normalize -- Whether to normalize the variables in the model. Preferably, keep it True.
    """

    # Indices
    model = ConcreteModel()
    model.nodes = Set(initialize=range(grid.n_nodes))
    model.lines = Set(initialize=range(grid.n_lines))
    # Variables
    model.V_nodes = Var(model.nodes)
    model.P_nodes = Var(model.nodes)
    model.I_lines = Var(model.lines)
    model.norm_factor = grid.ref_voltage if normalize else 1

    # Power flow
    model.power_balance = ConstraintList()
    for n1_ind, n1 in enumerate(grid.nodes):
        v_node = model.V_nodes[n1_ind]
        p_node = -v_node * sum([grid.Y[n1_ind, n2_ind] * model.V_nodes[n2_ind] for n2_ind in range(grid.n_nodes)])
        model.power_balance.add(model.P_nodes[n1_ind] == p_node)

    # Lines currents
    model.lines_current = ConstraintList()
    for line_ind, line in enumerate(grid.lines):
        node_from_ind = grid.nodes.index(line.node_from)
        node_to_ind = grid.nodes.index(line.node_to)
        i_line = line.g * (model.V_nodes[node_from_ind] - model.V_nodes[node_to_ind])
        model.lines_current.add(model.I_lines[line_ind] == i_line)
        model.I_lines[line_ind].setlb(line.i_min / model.norm_factor)
        model.I_lines[line_ind].setub(line.i_max / model.norm_factor)

    # Nodal constraints
    model.nodal_voltage = ConstraintList()
    model.nodal_power = ConstraintList()
    model.nodal_currents = ConstraintList()
    model.utilities_list = []
    model.generators_power = ConstraintList()
    for n1_ind, n1 in enumerate(grid.nodes):

        v_min, v_max = n1.v_min, n1.v_max
        p_min, p_max = max(n1.p_min, n1.p_demand_min), min(n1.p_max, n1.p_demand_max)
        i_min, i_max = n1.i_min, n1.i_max

        model.V_nodes[n1_ind].setlb(v_min / model.norm_factor)
        model.V_nodes[n1_ind].setub(v_max / model.norm_factor)
        model.P_nodes[n1_ind].setlb(p_min / model.norm_factor ** 2)
        model.P_nodes[n1_ind].setub(p_max / model.norm_factor ** 2)

        model.nodal_currents.add(model.P_nodes[n1_ind] - i_min / model.norm_factor * model.V_nodes[n1_ind] >= 0)
        model.nodal_currents.add(i_max / model.norm_factor * model.V_nodes[n1_ind] - model.P_nodes[n1_ind] >= 0)

        utility = model.P_nodes[n1_ind] * n1.utility_coef
        model.utilities_list.append(utility)

    # Objective
    model.utility = Objective(sense=maximize, expr=sum(model.utilities_list))
    return model
