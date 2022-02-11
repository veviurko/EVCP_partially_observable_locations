from src.scenario.process_evs_dundee import load_scenarios_csv, get_arrival_rate
from src.scenario.process_prices_entsoe import sample_random_prices
from src.scenario.scenario import Scenario
from src.grid.electrical_vehicle import EV
import pandas as pd
import numpy as np


class ScenarioGenerator:

    def __init__(self, t_start_hr, t_end_hr, ptu_size_minutes,
                 charging_time_mean_bounds, charging_time_std_bounds,
                 per_hour_demand_mean_bounds, per_hour_demand_std_bounds, std_price_factor=1000,
                 path_sessions='/home/gr1/Projects/DC_project/data/cp-data-mar-may-2018.csv',
                 path_prices='/home/gr1/Projects/DC_project/data/scenarios_entsoe_da_prices_NL_2020.csv'):

        """ ScenarioGenerator is used to generate scenarios. It stores the EVs arrival distribution parameters.
            Arrival rate is taken from the EV charging sessions dataset. Power price is also sampled from a dataset.
            t_start_hr, t_end_hr -- first and last timesteps of the simulation
            charging_time_mean_bounds, charging_time_std_bounds --  tuples, containing bounds for mean and std for
                                                                    the charging time.  Each sample, mean m and std s
                                                                    are sampled uniformly from these bounds. Then
                                                                    charging times are sampled from the  normal
                                                                     distribution N(m, s).
            per_hour_demand_mean_bounds, per_hour_demand_std_bounds -- same as above, but for per-hour demand. Per-hour
                                                                       demand is the EV's demand  divided by its
                                                                        parking time """

        self.t_start_hr = t_start_hr
        self.t_end_hr = t_end_hr
        self.ptu_size_minutes = ptu_size_minutes
        self.ptu_size_hr = ptu_size_minutes / 60
        self.timesteps_hr = np.arange(self.t_start_hr, self.t_end_hr + self.ptu_size_hr, self.ptu_size_hr)

        self.charging_time_mean_bounds = charging_time_mean_bounds
        self.charging_time_std_bounds = charging_time_std_bounds
        self.per_hour_demand_mean_bounds = per_hour_demand_mean_bounds
        self.per_hour_demand_std_bounds = per_hour_demand_std_bounds

        self.path_sessions = path_sessions
        self.path_prices = path_prices
        self.ev_charging_sessions = load_scenarios_csv(path_sessions)
        self.da_price_scenarios = pd.read_csv(path_prices)
        self.station_cons_to_use = ['50911_connector-2', '50692_connector-2',
                                    '51548_connector-2', '51547_connector-2',
                                    '51549_connector-2']

        self.arrival_rate = get_arrival_rate(self.timesteps_hr, self.ev_charging_sessions,
                                             self.station_cons_to_use, )

        self.std_price_factor = std_price_factor
        self.mean_price = 5e-4 * np.ones(self.timesteps_hr.shape)
        self.std_price = self.mean_price / std_price_factor

    def _get_mean_charging_time(self):
        mean_charging_time_raw = np.random.uniform(*self.charging_time_mean_bounds, size=self.timesteps_hr.shape)
        weights = np.exp(-(self.timesteps_hr - self.timesteps_hr[int(12 / self.ptu_size_hr)]) ** 2 / 500)
        return mean_charging_time_raw * weights

    def _get_std_charging_time(self):
        return np.random.uniform(*self.charging_time_std_bounds, size=self.timesteps_hr.shape)

    def _get_mean_per_hour_demand(self):
        return np.random.uniform(*self.per_hour_demand_mean_bounds, size=self.timesteps_hr.shape)

    def _get_std_per_hour_demand(self):
        return np.random.uniform(*self.per_hour_demand_std_bounds, size=self.timesteps_hr.shape)

    def _sample_power_price(self):
        return sample_random_prices(self.da_price_scenarios, self.timesteps_hr) / 1e6

    def generate(self, load_inds, n_scenarios, current_t_ind, known_evs, known_power_price=None):

        scenarios = []

        for sc_ind in range(n_scenarios):
            load_ind_business = {load_ind: np.zeros(len(self.timesteps_hr)) for load_ind in load_inds}

            for ev in known_evs:
                t_arr_ind = int(ev.t_arr_hr / self.ptu_size_hr)
                t_dep_ind = int(ev.t_dep_hr / self.ptu_size_hr)
                load_ind_business[ev.load_ind][t_arr_ind: t_dep_ind] = True

            sc_node_ind_business = dict(load_ind_business)
            sc_evs = list(known_evs)

            mean_charging_time = self._get_mean_charging_time()
            std_charging_time = self._get_std_charging_time()
            mean_per_hour_demand = self._get_mean_per_hour_demand()
            std_per_hour_demand = self._get_std_per_hour_demand()
            power_price = self._sample_power_price()
            if known_power_price is not None:
                power_price[: current_t_ind + 1] = known_power_price[: current_t_ind + 1]

            for t_ind in range(current_t_ind + 1, self.timesteps_hr.shape[0] - 1):
                for load_ind in load_inds:
                    if sc_node_ind_business[load_ind][t_ind]:
                        continue

                    if np.random.uniform() <= self.arrival_rate[t_ind]:
                        t_arr_ind = int(t_ind)
                        t_arr_hr = self.timesteps_hr[t_arr_ind]
                        t_charging_hr = np.random.normal(loc=mean_charging_time[t_ind],
                                                         scale=std_charging_time[t_ind])
                        t_charging_hr = max(self.ptu_size_hr, t_charging_hr)
                        t_dep_hr = min(24, self.ptu_size_hr * int((t_arr_hr + t_charging_hr) // self.ptu_size_hr))
                        t_dep_ind = int(t_dep_hr / self.ptu_size_hr)
                        t_charging_hr = t_dep_hr - t_arr_hr
                        per_hour_demand = np.random.normal(loc=mean_per_hour_demand[t_ind],
                                                           scale=std_per_hour_demand[t_ind])
                        demand = t_charging_hr * per_hour_demand

                        price = np.random.normal(loc=self.mean_price[t_ind], scale=self.std_price[t_ind])

                        ev = EV(load_ind, 0, demand, demand, t_arr_hr, t_dep_hr, price)
                        sc_evs.append(ev)
                        sc_node_ind_business[load_ind][t_arr_ind: t_dep_ind] = True

            scenarios.append(Scenario(load_inds, self.timesteps_hr, sc_evs, power_price))
        return scenarios
