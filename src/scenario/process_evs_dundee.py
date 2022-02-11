from src.scenario.process_datetimes import date_time_to_datetime
from collections import defaultdict
from datetime import timedelta
import pandas as pd
import numpy as np
import random


def load_scenarios_csv(path_to_csv):
    ev_charging = pd.read_csv(path_to_csv).dropna()
    ev_charging = ev_charging[ev_charging['Total kWh'] > 0].reset_index(drop=True)
    st_datetimes_list = []
    e_datetimes_list = []
    min_charged_list = []

    for (st_date, st_time, e_date, e_time) in ev_charging[['Start Date', 'Start Time',
                                                           'End Date', 'End Time']].values:
        st_datetime = date_time_to_datetime(st_date, st_time)
        e_datetime = date_time_to_datetime(e_date, e_time)
        st_datetimes_list.append(st_datetime)
        e_datetimes_list.append(e_datetime)
        min_charged_list.append((e_datetime - st_datetime).seconds // 60)

    ev_charging['st_dt'] = st_datetimes_list
    ev_charging['e_dt'] = e_datetimes_list
    ev_charging['t_charged'] = min_charged_list
    ev_charging['CP ID CON'] = (ev_charging['CP ID'].apply(lambda x: str(x))
                                + ev_charging['Connector'].apply(lambda x: '_connector-' + str(x)))

    new_columns = ['event_id', 'station_id', 'connector', 'start_date', 'start_time', 'end_date', 'end_time',
                   'kwh_charged', 'cost', 'site', 'group', 'model', 'start_datetime', 'end_datetime', 'time_charged',
                   'station_connector_id']
    ev_charging.columns = new_columns

    return ev_charging


def make_two_digit_str(num):
    if num < 10:
        return '0' + str(num)
    else:
        return str(num)


def get_cp_scenarios(station_con_id, ev_charging):
    station_con_ev_charging = ev_charging[ev_charging['station_connector_id'] == station_con_id]
    dates = station_con_ev_charging['start_date'].unique()
    per_date_loads = defaultdict(list)
    for d in dates:
        date_cp_ev_charging = station_con_ev_charging[station_con_ev_charging['start_date'] == d]
        for st_date, st_t, e_date, e_t, power in date_cp_ev_charging[['start_date', 'start_time',
                                                                      'end_date', 'end_time', 'kwh_charged']].values:
            st_hour, st_minutes = map(int, st_t.split(':'))
            e_hour, e_minutes = map(int, e_t.split(':'))
            st_ind = st_hour * 60 + st_minutes
            e_ind = e_hour * 60 + e_minutes
            if st_date == e_date:
                per_date_loads[d].append((st_t, e_t, power))
            else:
                date_dt = date_time_to_datetime(st_date, st_t)
                date_next_dt = date_dt + timedelta(days=1)
                d_next = '%s/%s/%s' % (make_two_digit_str(date_next_dt.day),
                                       make_two_digit_str(date_next_dt.month),
                                       date_next_dt.year)
                power_d = (24 * 60 - st_ind) / (24 * 60 - st_ind + e_ind) * power
                power_d_next = power - power_d

                per_date_loads[d].append((st_t, '23:59', power_d))
                per_date_loads[d_next].append(('00:00', e_t, power_d_next))
    return per_date_loads


def get_arrival_rate(timesteps_hr, ev_charging_sessions, station_cons_to_use, round_minutes=1):
    time_to_arrival_rate = defaultdict(list)
    for station_con_id in station_cons_to_use:

        per_date_loads = get_cp_scenarios(station_con_id, ev_charging_sessions)
        for loads in per_date_loads.values():
            station_was_free = np.ones(int(24 * 60 / round_minutes), dtype='bool')
            arrival_inds = set()
            for t_arr_str, t_dep_str, _ in loads:
                hr_arr, min_arr = map(int, t_arr_str.split(':'))
                hr_dep, min_dep = map(int, t_dep_str.split(':'))
                min_arr = round_minutes * int(min_arr / round_minutes)
                min_dep = round_minutes * int(min_dep / round_minutes)

                ind_arr = int((60 * hr_arr + min_arr) / round_minutes)
                ind_dep = int((60 * hr_dep + min_dep) / round_minutes)
                station_was_free[ind_arr + 1: ind_dep] = False
                arrival_inds.add(ind_arr)

            for t_ind in range(station_was_free.shape[0]):
                if station_was_free[t_ind]:
                    time_to_arrival_rate[t_ind].append(int(t_ind in arrival_inds))

        time_to_arrival_rate_array = np.zeros(24 * 60)
        for key, val in time_to_arrival_rate.items():
            time_to_arrival_rate_array[round_minutes * key: round_minutes * (key + 1)] = np.mean(val)

    arrival_rate = np.convolve(time_to_arrival_rate_array, np.ones(50), 'same') / 50
    arrival_rate_avg = np.ones_like(timesteps_hr, dtype='float32')
    ptu_size_minutes = int(60 * (timesteps_hr[1] - timesteps_hr[0]))
    for ind in range(arrival_rate_avg.shape[0] - 1):
        minute_start = ind * ptu_size_minutes
        minute_end = (ind + 1) * ptu_size_minutes
        prob_arrive = 1 - np.prod(1 - arrival_rate[minute_start: minute_end])
        arrival_rate_avg[ind] = np.float(prob_arrive)
    arrival_rate_avg[-1] = arrival_rate_avg[0]

    return arrival_rate_avg


def get_charging_time_mean_std(timesteps_hr, ev_charging_sessions, station_cons_to_use):
    st_con_ev_charging_sessions = ev_charging_sessions[
        ev_charging_sessions['station_connector_id'].isin(station_cons_to_use)]

    ptu_size_minutes = int(60 * (timesteps_hr[1] - timesteps_hr[0]))
    st_time_in_minutes_rounded = st_con_ev_charging_sessions['start_datetime'].apply(lambda x: (x.hour +
                                                                                                int(ptu_size_minutes *
                                                                                                    (x.minute //
                                                                                                     ptu_size_minutes))
                                                                                                / 60)
                                                                                     )
    time_arrival_to_charging_time = defaultdict(list)
    for (st_time, ch_time,) in zip(st_time_in_minutes_rounded, st_con_ev_charging_sessions['time_charged']):
        time_arrival_to_charging_time[st_time].append(ch_time)

    mean_charging_time = np.empty_like(timesteps_hr)
    std_charging_time = np.empty_like(timesteps_hr)
    for t_ind, t_hr in enumerate(timesteps_hr):
        mean_charging_time[t_ind] = np.mean(time_arrival_to_charging_time[t_hr])
        std_charging_time = np.std(time_arrival_to_charging_time[t_hr])

    mean_charging_time = np.convolve(mean_charging_time, np.ones(2), 'same') / 2
    std_charging_time = np.convolve(std_charging_time, np.ones(2), 'same') / 2
    return mean_charging_time, std_charging_time
