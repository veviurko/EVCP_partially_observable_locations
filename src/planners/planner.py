import numpy as np
import time


class Planner:

    def __init__(self,
                 name_base='Planner',
                 observe_ev_locations='full',
                 future_model='full',
                 n_future_samples=4,
                 grid_transformation=None,
                 normalize=True,
                 obj_factors=(1, ),
                 tee=False,
                 accept_unknown_solution=False,
                 debugging=False,
                 use_weird_sur_grid=False,
                 unify_grid=False,
                 **solver_options):

        # Observability: 'full', 'present', 'past', 'blind'
        assert observe_ev_locations in ['full', 'present', 'past', 'blind']
        assert future_model in ['known-future', 'sample', 'no-future']
        assert grid_transformation in [None, 'parallel', 'single-node']
        self.observe_ev_locations = observe_ev_locations
        self.future_model = future_model
        self.n_future_samples = n_future_samples
        self.grid_transformation = grid_transformation
        self.unify_grid = unify_grid

        self.normalize = normalize
        self.obj_factors = [1, 100, 0.01, 2500, 0.001] if obj_factors is None else obj_factors
        self.tee = tee
        self.accept_unknown_solution = accept_unknown_solution
        self.solver_options = solver_options
        self.debugging = debugging

        grid_transformation_str = grid_transformation if grid_transformation is not None else ''
        self.name = (name_base +
                     '_normalize=%s_future=%s_ev-locations=%s_%s' % (normalize, future_model,
                                                                     observe_ev_locations, grid_transformation))
        if unify_grid:
            self.name = self.name + '-unified'

        self.use_weird_sur_grid = use_weird_sur_grid
        if use_weird_sur_grid:
            self.name = self.name + '-weird'

    def solve(self, true_grid, surrogate_grid, sampled_scenarios,
              t_current_ind, SOC_evs_current, obj_factor, norm_factor):
        raise NotImplementedError

    def step(self, true_grid, surrogate_grid, sampled_scenarios, per_scenario_ev_maps,
             t_current_ind, SOC_evs_current):
        #P_evs_now = np.empty(max([len(sc.evs) for sc in sampled_scenarios]))
        time_start = time.time()
        norm_factors = [true_grid.ref_voltage, true_grid.ref_voltage * 2,
                        true_grid.ref_voltage * 5] if self.normalize else [1]

        if self.debugging:
            print('Running in debugging mode with obj_factor=%.2f, norm_factor=%.2f' % (self.obj_factors[0],
                                                                                        norm_factors[0]))
            P_evs_now = self.solve(true_grid, surrogate_grid, sampled_scenarios, t_current_ind,
                                   SOC_evs_current, self.obj_factors[0], norm_factors[0])


        stop = False
        for j, norm_factor in enumerate(norm_factors):
            if stop:
                break
            for i, obj_factor in enumerate(self.obj_factors):
                attempt = (i, j)
                try:
                    P_evs_now, P_nodes_list, V_nodes_list, SOC_evs_list = self.solve(true_grid, surrogate_grid, sampled_scenarios,
                                                                                     t_current_ind, SOC_evs_current, obj_factor,
                                                                                     norm_factor)
                    '''P_evs_now = self.solve(true_grid, surrogate_grid,
                                           sampled_scenarios,
                                           t_current_ind, SOC_evs_current,
                                           obj_factor,
                                           norm_factor)'''
                    stop = True
                    break
                except:
                    print('Attempt %s with obj_factor=%.3f, norm_factor=%d failed,'
                          ' retrying planner %s' % (attempt, obj_factor, norm_factor, self.name))
        P_evs_now_transformed = np.zeros_like(P_evs_now)
        for new_ev_ind in range(len(P_evs_now)):
            old_ev_ind = per_scenario_ev_maps
        plan = {'P_evs_now': P_evs_now,
                'P_nodes_list': np.mean(P_nodes_list, 0),
                'V_nodes_list': np.mean(V_nodes_list, 0),
                'SOC_evs_list': np.mean(SOC_evs_list, 0),
                'planning time': time.time() - time_start}
        #print("PLAN", plan['P_evs_now'])
        return plan
