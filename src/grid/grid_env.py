from src.scenario.scenario_generator import ScenarioGenerator
from src.executors.exact.solve_opf import solve
from src.scenario.scenario import Scenario
from src.grid.grid import Grid
import numpy as np


class GridEnv:
    def __init__(self,
                 grid: Grid,
                 scenario: Scenario,
                 scenario_generator: ScenarioGenerator,
                 tee: bool = False):

        """ Environment clas. Combines the DC grid with the information about EVs and power price.
            grid: DC grid
            scenario: scenario specifying EVs and power price
            scenario_generator: ScenarioGenerator object, contains information about all
                                EV and power price related distributions """

        self.grid = grid
        self.scenario = scenario
        self.scenario_generator = scenario_generator
        self.tee = tee

        self.t_start_ind = 0
        self.t_end_ind = scenario.t_end_ind
        self.timesteps_hr = scenario.timesteps_hr
        self.t_ind = 0
        self.ptu_size_hr = scenario.ptu_size_hr

        self.V_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.P_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.I_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.I_lines = np.empty((self.grid.n_lines, self.timesteps_hr.shape[0]))
        self.SOC_evs = np.nan * np.ones((len(self.scenario.evs), self.timesteps_hr.shape[0]))

    @property
    def t_hr(self):
        return self.timesteps_hr[self.t_ind]

    @property
    def finished(self):
        return self.t_ind > self.t_end_ind

    @property
    def current_SOC(self):
        return np.minimum([ev.soc_max for ev in self.scenario.evs], np.maximum(0, self.SOC_evs[:, self.t_ind]))

    def reset(self, ):
        V_nodes, P_nodes, I_nodes, I_lines = self.grid.get_init_state()
        self.grid.apply_state(V_nodes, P_nodes, I_nodes, I_lines)
        utility_coefs = np.zeros(self.grid.n_nodes)
        for load_ind in self.grid.load_inds:
            utility_coefs[load_ind] = 100
        for gen_ind in self.grid.gen_inds:
            utility_coefs[gen_ind] = 1

        self.grid.update_demand_and_price(np.zeros(self.grid.n_nodes), np.zeros(self.grid.n_nodes), utility_coefs)
        self.t_ind = 0
        self.V_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.P_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.I_nodes = np.empty((self.grid.n_nodes, self.timesteps_hr.shape[0]))
        self.I_lines = np.empty((self.grid.n_lines, self.timesteps_hr.shape[0]))
        self.SOC_evs = np.zeros((len(self.scenario.evs), self.timesteps_hr.shape[0]))
        for ev_ind, ev in enumerate(self.scenario.evs):
            if self.t_hr == ev.t_arr_hr:
                self.SOC_evs[ev_ind, self.t_ind] = ev.soc_arr

    def step(self, p_demand_min, p_demand_max, utility_coefs, normalize_opf=False):
        #print('Stepping:', p_demand_min.round(2), '\n', p_demand_max.round(2))
        for load_ind in self.grid.load_inds:
            ev_at_t_at_load = self.scenario.load_evs_presence[load_ind][self.t_ind]
            active_evs_at_t_at_node = [ev for ev in ev_at_t_at_load if ev.t_dep_hr > self.t_hr]
            if len(active_evs_at_t_at_node) > 0:
                ev = active_evs_at_t_at_node[0]
                ev_ind = self.scenario.evs.index(ev)
                load_p_max = (ev.soc_max - self.SOC_evs[ev_ind, self.t_ind]) / self.scenario.ptu_size_hr
                p_demand_max[load_ind] = min(load_p_max, p_demand_max[load_ind])
        p_demand_max[p_demand_max < p_demand_min] = p_demand_min[p_demand_max < p_demand_min] + 1e-10
        self.grid.update_demand_and_price(p_demand_min-1e-8, p_demand_max + 1e-8, utility_coefs)
        #print('After corrections:', p_demand_min.round(2), '\n', p_demand_max.round(2))
        # self.tee = True
        #print('LB', p_demand_min)
        #print('UB', p_demand_max)
        loads_p_demand_min = p_demand_min[self.grid.load_inds]
        loads_p_demand_max = p_demand_max[self.grid.load_inds]

        if loads_p_demand_min.max() == loads_p_demand_max.max() == 0:
            model = None
            V_nodes = np.array(([n.v_nominal for n in self.grid.nodes]))
            P_nodes = np.zeros(self.grid.n_nodes)
            I_nodes = np.zeros(self.grid.n_nodes)
            I_lines = np.zeros(self.grid.n_lines)
        else:
            model, V_nodes, P_nodes, I_nodes, I_lines = solve(self.grid, tee=self.tee, normalize=normalize_opf)

        self.grid.apply_state(V_nodes, P_nodes, I_nodes, I_lines)
        self.V_nodes[:, self.t_ind] = np.copy(V_nodes)
        self.P_nodes[:, self.t_ind] = np.copy(P_nodes)
        self.I_nodes[:, self.t_ind] = np.copy(I_nodes)
        self.I_lines[:, self.t_ind] = np.copy(I_lines)

        self.t_ind += 1
        if not self.finished:
            for ev_ind, ev in enumerate(self.scenario.evs):
                if self.t_hr == ev.t_arr_hr:
                    self.SOC_evs[ev_ind, self.t_ind] = ev.soc_arr
                elif ev.t_arr_hr < self.t_hr <= ev.t_dep_hr:
                    old_soc = self.SOC_evs[ev_ind, self.t_ind - 1]
                    new_soc = old_soc + self.ptu_size_hr * self.P_nodes[ev.load_ind, self.t_ind - 1]
                    self.SOC_evs[ev_ind, self.t_ind] = np.copy(new_soc)

    def observe_scenario(self, know_future=False):
        if know_future:
            return self.scenario
        else:
            return self.scenario.create_scenario_unknown_future(self.t_ind)

    def get_cost_coefs(self):
        utility_coefs = np.zeros(self.grid.n_nodes)
        utility_coefs[self.grid.gen_inds] = self.scenario.power_price[self.t_ind]
        for load_ind in self.grid.load_inds:
            ev_at_t_at_load = self.scenario.load_evs_presence[load_ind][self.t_ind]
            active_evs_at_t_at_node = [ev for ev in ev_at_t_at_load if ev.t_dep_hr > self.t_hr]
            if len(active_evs_at_t_at_node) > 0:
                assert len(active_evs_at_t_at_node) == 1, "More than 1 EV at load %d" % load_ind
                ev = active_evs_at_t_at_node[0]
                utility_coefs[load_ind] = ev.utility_coef

        return utility_coefs

    def generate_possible_futures(self, n_scenarios):
        return self.scenario_generator.generate(self.grid.n_loads, n_scenarios, self.t_ind,
                                                self.scenario.get_evs_known_at_t_ind(self.t_ind))