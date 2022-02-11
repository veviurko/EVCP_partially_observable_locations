from src.planners.exact._create_model import create_model
from src.planners.exact._read_model import read_model
from src.planners.planner import Planner
from pyomo.environ import *


class ExactPlanner(Planner):

    def __init__(self,
                 opf_method='lossless',
                 observe_ev_locations='full',
                 future_model='known-future',
                 n_future_samples=5,
                 grid_transformation=None,
                 normalize=True,
                 obj_factors=(1, ),
                 tee=False,
                 accept_unknown_solution=False,
                 debugging=False,
                 **solver_options):

        assert opf_method in ['exact', 'lossless'], ('Unknown opf method %s' % opf_method)
        self.opf_method = opf_method
        name_base = 'ExactPlanner' if opf_method == 'exact' else 'LosslessPlanner'
        super().__init__(name_base, observe_ev_locations, future_model, n_future_samples,
                         grid_transformation, normalize, obj_factors, tee, accept_unknown_solution,
                         debugging, **solver_options)

    def create_solver(self, ):
        solver = SolverFactory('ipopt') if self.opf_method == 'exact' else SolverFactory('glpk')
        #solver = SolverFactory('ipopt')
        for key, val in self.solver_options.items():
            solver.options[key] = val
        return solver

    def solve(self, true_grid, surrogate_grid, sampled_scenarios,
              t_current_ind, SOC_evs_current, obj_factor, norm_factor):

        model = create_model(self.opf_method, true_grid, surrogate_grid, sampled_scenarios, t_current_ind,
                             SOC_evs_current, obj_factor=obj_factor, norm_factor=norm_factor)
        solver = self.create_solver()
        solver.solve(model, tee=self.tee)
        P_evs_now, P_nodes_now = read_model(model, surrogate_grid)
        #print('P_evs_now:', P_evs_now.round())
        #print('P_nodes_now', P_nodes_now.round())
        #print()
        #print('Solution:', P_evs_now)
        #print('P_nodes_now', P_nodes_now)
        return P_evs_now, [[]], [[]], [[]]
