from src.grid.electrical_vehicle import EV
from collections import defaultdict
from typing import List
import numpy as np


class Scenario:

    def __init__(self,
                 load_inds: list,
                 timesteps_hr: np.ndarray,
                 evs: List[EV],
                 power_price: np.ndarray,
                 ):

        """ Scenario aggregates information about EVs and power price .
            load_inds -- indicis of the load nodes in the grid
            timesteps_hr -- array of the timesteps
            evs -- list of the EVs
            power_price -- array specifying power price. Should have the same shape as timesteps_hr """

        self.load_inds = load_inds
        self.n_loads = len(load_inds)
        self.power_price = power_price

        self._setup_times(timesteps_hr)
        self._setup_evs(evs)

        assert power_price.shape == self.timesteps_hr.shape, 'Timesteps and power price shapes must be equal'

    def _setup_times(self, timesteps_hr):

        self.timesteps_hr = timesteps_hr

        self.t_start_hr = timesteps_hr[0]
        self.t_start_ind = 0
        self.t_end_hr = timesteps_hr[-1]
        self.n_timesteps = len(self.timesteps_hr)
        self.t_end_ind = self.n_timesteps - 1

        self.ptu_size_hr = timesteps_hr[1] - timesteps_hr[0]
        self.ptu_size_minutes = int(60 * self.ptu_size_hr)

    def _setup_evs(self, evs):

        self.evs = evs

        self.load_evs_presence = {load_ind: defaultdict(list) for load_ind in self.load_inds}
        self.ev_status = defaultdict(dict)
        self.t_ind_arrivals = defaultdict(list)
        self.t_ind_departures = defaultdict(list)
        self.t_ind_charging_evs = defaultdict(list)
        self.load_ind_business = {load_ind: np.zeros(self.n_timesteps) for load_ind in self.load_inds}

        for ev in evs:
            # ev.utility_coef /= self.norm_factor
            t_arr_ind = int(ev.t_arr_hr / self.ptu_size_hr)
            t_dep_ind = int(ev.t_dep_hr / self.ptu_size_hr)
            assert t_arr_ind == ev.t_arr_hr / self.ptu_size_hr and t_dep_ind == ev.t_dep_hr / self.ptu_size_hr, \
                'EVs arrival and departure times should be rounded to PTU size !'
            self.load_ind_business[ev.load_ind][t_arr_ind: t_dep_ind] = True
            for t_ind in range(self.timesteps_hr.shape[0]):
                if t_ind < t_arr_ind:
                    self.ev_status[ev][t_ind] = 'inactive'

                elif t_ind == t_arr_ind:
                    self.ev_status[ev][t_ind] = 'arrive'
                    self.t_ind_arrivals[t_ind].append(ev)
                    self.load_evs_presence[ev.load_ind][t_ind].append(ev)

                elif t_arr_ind < t_ind < t_dep_ind:
                    self.ev_status[ev][t_ind] = 'active'
                    self.t_ind_charging_evs[t_ind].append(ev)
                    self.load_evs_presence[ev.load_ind][t_ind].append(ev)

                elif t_ind == t_dep_ind:
                    self.ev_status[ev][t_ind] = 'depart'
                    self.t_ind_departures[t_ind].append(ev)
                    self.load_evs_presence[ev.load_ind][t_ind].append(ev)

                elif t_ind > t_dep_ind:
                    self.ev_status[ev][t_ind] = 'inactive'

    def get_evs_known_at_t_ind(self, t_ind: int) -> List[EV]:
        evs_known_at_t_ind = [ev for ev in self.evs if int(ev.t_arr_hr / self.ptu_size_hr) <= t_ind]
        return evs_known_at_t_ind

    def create_scenario_unknown_future(self, t_ind):
        evs_known_at_t_ind = self.get_evs_known_at_t_ind(t_ind)
        return Scenario(self.load_inds, self.timesteps_hr, evs_known_at_t_ind, self.power_price)
