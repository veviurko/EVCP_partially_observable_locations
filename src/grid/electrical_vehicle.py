import numpy as np


class EV:

    def __init__(self,
                 load_ind: int,
                 soc_arr: float,
                 soc_goal: float,
                 soc_max: float,
                 t_arr_hr: float,
                 t_dep_hr: float,
                 utility_coef: float,
                 p_max: float = 0,
                 p_min: float = -np.inf, ):

        """ EV class is used to model the electric vehicles.
            load_ind -- index of the load where the EV is charged at
            soc_arr, soc_goal, soc_max -- arrival, target and maximum state-of-charge in Wh
            t_arr_hr, t_dep_hr -- arrival and departure times
            utility_coef -- linear utility coefficient
            p_max, p_min -- maximum and minimum charging rate in W """

        self.load_ind = load_ind

        self.soc_arr = soc_arr
        self.soc_goal = soc_goal
        self.soc_max = soc_max
        self.soc = np.nan

        self.t_arr_hr = t_arr_hr
        self.t_dep_hr = t_dep_hr

        self.p_max = p_max
        self.p_min = p_min

        self.utility_coef = utility_coef

    def __repr__(self):
        return 'EV_at_%d_t_arr_hr=%.1f_t_dep_hr=%.1f' % (self.load_ind, self.t_arr_hr, self.t_dep_hr)

    def __str__(self):
        return 'EV_at_%d_t_arr_hr=%.1f_t_dep_hr=%.1f' % (self.load_ind, self.t_arr_hr, self.t_dep_hr)

    @property
    def free_capacity(self):
        if not np.isnan(self.soc):
            return self.soc_max - self.soc
        else:
            return self.soc_max - self.soc_arr

    def arrive(self):
        self.soc = self.soc_arr

    def charge(self, p, dt_hr):
        p_kwh = p * dt_hr
        soc_after = self.soc - p_kwh
        assert 0 - 0.333 <= soc_after <= self.soc_max + 0.333, ('SOC of load %s is out of required range. '
                                                                'SOC before =%.1f, SOC after =%.1f, SOC max = %.1f' %
                                                                (self, self.soc, soc_after, self.soc_max))
        soc_after = np.clip(soc_after, 0.001, self.soc_max - 0.001)
        self.soc = soc_after


