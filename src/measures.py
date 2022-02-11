import numpy as np


def measure_loads_misstmatch(results, scenario, grid, average=False, gap=0.99):
    P_loads_plan = results['P_nodes_plan'][grid.load_inds]
    P_loads_ex = results['P_nodes'][grid.load_inds]

    missmatch = np.zeros((grid.n_loads, scenario.n_timesteps), dtype='int')
    for t_ind in range(scenario.n_timesteps):
        for load_ind, load in enumerate(grid.loads):
            p_plan = P_loads_plan[load_ind, t_ind]
            p_ex = P_loads_ex[load_ind, t_ind]
            missmatch[load_ind, t_ind] = p_plan - p_ex

    missmatch = missmatch.sum(0)
    if average:
        missmatch = np.mean(missmatch)
    return missmatch


def measure_lines_misstmatch(results, scenario, grid, average=False, gap=0.99):
    I_lines_plan = results['I_lines_plan']
    I_lines_ex = results['I_lines']

    missmatch = np.zeros((grid.n_lines, scenario.n_timesteps),)
    for t_ind in range(scenario.n_timesteps):
        for line_ind, line in enumerate(grid.lines):
            i_plan = I_lines_plan[line_ind, t_ind]
            i_ex = I_lines_ex[line_ind, t_ind]
            missmatch[line_ind, t_ind] = np.abs(i_plan - i_ex)

    missmatch = missmatch.sum(0)
    if average:
        missmatch = np.mean(missmatch)
    return missmatch


def measure_lines_at_limit(results, scenario, grid, average=False, gap=0.01, use_plan=False):
    I_lines = results['I_lines_plan'] if use_plan else results['I_lines']
    line_at_limit = np.zeros((grid.n_lines, scenario.n_timesteps), dtype='int')
    for t_ind in range(scenario.n_timesteps):
        for line_ind, line in enumerate(grid.lines):
            is_at_limit = ((1 - gap) * line.i_max <= np.abs(I_lines[line_ind, t_ind])
                           <= (1 + gap) * line.i_max)
            line_at_limit[line_ind, t_ind] = (is_at_limit)
    line_at_limit = line_at_limit.sum(0)
    if average:
        line_at_limit = np.mean(line_at_limit)
    return line_at_limit


def measure_soc_percentage(results, scenario, average=True):
    soc_percentage = []
    for soc_curve, ev in zip(results['SOC_evs'], scenario.evs):
        t_dep_ind = int(ev.t_dep_hr / scenario.ptu_size_hr)
        soc_percentage.append(soc_curve[t_dep_ind] / ev.soc_goal)
    soc_percentage = np.mean(soc_percentage) if average else np.array(soc_percentage)
    return soc_percentage


def measure_unmet_demand(results, scenario, grid, average=True):
    unmet_demand = []
    for soc_curve, ev in zip(results['SOC_evs'], scenario.evs):
        t_dep_ind = int(ev.t_dep_hr / scenario.ptu_size_hr)
        unmet_demand.append(ev.soc_goal - soc_curve[t_dep_ind])
    unmet_demand = np.mean(unmet_demand) if average else np.array(unmet_demand)
    return unmet_demand


def measure_charged_evs(results, scenario, grid, charged_threshold=0.999, average=True):
    soc_percentage = measure_soc_percentage(results, scenario, average=False)
    charged_evs = soc_percentage >= charged_threshold
    charged_evs = np.mean(charged_evs) if average else np.array(charged_evs)
    return charged_evs


def measure_wealth(results, scenario, grid):
    wealth = []
    for ev_ind, ev in enumerate(scenario.evs):
        t_dep_ind = int(ev.t_dep_hr / scenario.ptu_size_hr)
        wealth.append(results['SOC_evs'][ev_ind, t_dep_ind] * ev.utility_coef)
    price_power = np.dot(results['P_nodes'][grid.gen_inds].sum(0), scenario.power_price)
    return np.sum(wealth) + price_power


def measure_per_load_soc_percentage(results, scenario, grid, average=True):
    soc_percentage = [[] for _ in range(grid.n_loads)]
    for soc_curve, ev in zip(results['SOC_evs'], scenario.evs):
        load_ind = grid.load_inds.index(ev.load_ind)
        t_dep_ind = int(ev.t_dep_hr / scenario.ptu_size_hr)
        soc_percentage[load_ind].append(soc_curve[t_dep_ind] / ev.soc_goal)
    return np.array([np.mean(load_soc) for load_soc in soc_percentage]) if average else soc_percentage


def measure_per_load_charged_evs(results, scenario, grid, charged_threshold=0.999, average=True):
    soc_percentage = measure_per_load_soc_percentage(results, scenario, grid, average=False)
    charged_evs = [np.mean([soc >= charged_threshold for soc in load_soc]) for load_soc in soc_percentage]
    return charged_evs


def measure_per_load_wealth(results, scenario, grid):
    wealth = [[] for _ in range(grid.n_loads)]
    for ev_ind, ev in enumerate(scenario.evs):
        load_ind = grid.load_inds.index(ev.load_ind)
        t_dep_ind = int(ev.t_dep_hr / scenario.ptu_size_hr)
        wealth[load_ind].append(results['SOC_evs'][ev_ind, t_dep_ind] * ev.utility_coef)
    return np.array([np.mean(load_w) for load_w in wealth])
