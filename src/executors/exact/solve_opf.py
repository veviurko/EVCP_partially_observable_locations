from src.executors.exact.create_model import create_model
from src.executors.exact.read_model import read_model
from src.grid.grid import Grid
from pyomo.environ import *


def solve(grid: Grid, normalize: bool = False, tee: bool = False, return_solution: bool = False):
    """ Solve the OPF problem for the grid. Creates the model, optimizes it and returns the solution. """
    model = create_model(grid, normalize=normalize)
    solver = SolverFactory('ipopt')
    solution = solver.solve(model, tee=tee)
    V_nodes, P_nodes, I_nodes, I_lines = read_model(model)
    if not return_solution:
        return model, V_nodes, P_nodes, I_nodes, I_lines
    else:
        return solution, model, V_nodes, P_nodes, I_nodes, I_lines
