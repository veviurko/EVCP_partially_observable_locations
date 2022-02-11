from src.planners.socp._create_model import create_model
from src.planners.socp._read_model import read_model
from mosek.fusion import AccSolutionStatus
from src.planners.planner import Planner
import sys


class SOCPPlanner(Planner):

    def __init__(self,
                 observe_ev_locations='full',
                 future_model='known-future',
                 n_future_samples=5,
                 grid_transformation=None,
                 normalize=True,
                 obj_factors=(1, ),
                 tee=False,
                 accept_unknown_solution=False,
                 debugging=False,
                 use_weird_sur_grid=False,
                 unify_grid=False,
                 **solver_options):

        name_base = 'SOCPPlanner'
        super().__init__(name_base, observe_ev_locations, future_model, n_future_samples,
                         grid_transformation, normalize, obj_factors, tee, accept_unknown_solution,
                         debugging, use_weird_sur_grid, unify_grid, **solver_options)

    def solve(self, true_grid, surrogate_grid, sampled_scenarios,
              t_current_ind, SOC_evs_current, obj_factor, norm_factor):

        model = create_model(true_grid, surrogate_grid, sampled_scenarios, t_current_ind, SOC_evs_current,
                             obj_factor=obj_factor, norm_factor=norm_factor, **self.solver_options)
        if self.tee:
            model.setLogHandler(sys.stdout)
        model.solve()
        if self.accept_unknown_solution:
            model.acceptedSolutionStatus(AccSolutionStatus.Anything)
        P_evs_now, P_nodes_list, V_nodes_list, SOC_evs_list = read_model(model, surrogate_grid)
        self.model = model
        return P_evs_now, P_nodes_list, V_nodes_list, SOC_evs_list
