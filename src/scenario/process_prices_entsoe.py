import numpy as np


def sample_random_prices(da_price_scenarios, timesteps_hr):
    prices = np.empty_like(timesteps_hr)

    ind = np.random.randint(0, da_price_scenarios.shape[0] - 1)
    hourly_prices = np.concatenate([da_price_scenarios.iloc[ind].values[1:],
                                    da_price_scenarios.iloc[ind + 1].values[-1:]])

    for t_ind, t_hr in enumerate(timesteps_hr):
        if int(t_hr) == t_hr:
            p = hourly_prices[int(t_hr)]

        else:
            prev_hour = int(np.floor(t_hr))
            next_hour = int(np.ceil(t_hr))
            w_prev = t_hr - prev_hour
            w_next = next_hour - t_hr
            p = w_prev * hourly_prices[prev_hour] + w_next * hourly_prices[next_hour]
        prices[t_ind] = np.maximum(p, 1e-6)
    return prices
