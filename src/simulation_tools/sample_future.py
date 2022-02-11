

def sample_future(env, planner,):
    if planner.future_model == 'known-future':
        scenarios = [env.scenario]
    elif planner.future_model == 'sample':
        scenarios = env.scenario_generator.generate(env.grid.load_inds, planner.n_future_samples, env.t_ind,
                                                    env.scenario.get_evs_known_at_t_ind(env.t_ind))
    elif planner.future_model == 'no-future':
        scenarios = [env.scenario.create_scenario_unknown_future(env.t_ind)]
    else:
        raise NotImplementedError('Future model = %s is not implemented' % planner.future_model)
    return scenarios
