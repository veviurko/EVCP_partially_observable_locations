import matplotlib.pyplot as plt
import numpy as np


def plot_performance(results_dict, planner_names_use, planner_names_dict, metrics_to_plot, metrics_normalize,
                     filter_by, plot_by, group_by, plot_by_name, group_by_name, group_by_units,
                     sc_inds_list, figsize, plt_config, pl_baseline, path_to_project, name,
                     y_label_per_metric=None, y_lim_per_metric=None,
                     save=False):

    plt.rc('font', size=plt_config['font_size'])  # controls default text sizes
    plt.rc('axes', titlesize=plt_config['axes_t_size'])  # fontsize of the axes title
    plt.rc('axes', labelsize=plt_config['axes_l_size'])  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=plt_config['xtick_size'])  # fontsize of the tick labels
    plt.rc('ytick', labelsize=plt_config['ytick_size'])  # fontsize of the tick labels
    plt.rc('legend', fontsize=plt_config['legend_size'])  # legend fontsize
    plt.rc('figure', titlesize=plt_config['title_size'])  # fontsize of the figure title

    grid_names_list = [gn for gn in results_dict.keys() if filter_by(gn)]
    group_by_values_list = [group_by(gn) for gn in grid_names_list]
    group_by_values_unique = sorted(list(set(group_by_values_list)))

    n_row_subplots = len(group_by_values_unique)
    n_cols_subplots = len(metrics_to_plot)

    fig, axes = plt.subplots(n_row_subplots, n_cols_subplots, figsize=figsize)
    axes = np.reshape(axes, (n_row_subplots, n_cols_subplots))

    per_metric_ymaxs = [-np.inf for metric in metrics_to_plot]
    per_metric_ymins = [np.inf for metric in metrics_to_plot]

    for row_ind, g_value in enumerate(group_by_values_unique):
        for col_ind, (metric_name, normalize) in enumerate(zip(metrics_to_plot, metrics_normalize)):
            grid_names_grouped_list = [gn for gn, gn_g_val in zip(grid_names_list, group_by_values_list)
                                       if gn_g_val == g_value]
            x_values_list = sorted([plot_by(gn) for gn in grid_names_grouped_list])
            grid_names_grouped_list = sorted(grid_names_grouped_list, key=plot_by)

            for pl_name_full in planner_names_use:
                pl_name_short = planner_names_dict[pl_name_full]
                planner_y_values_list = []
                planner_y_errors_list = []

                for x_val, gn in zip(x_values_list, grid_names_grouped_list):
                    yi_all_values = np.array([results_dict[gn][pl_name_full][metric_name][sc_ind]
                                              for sc_ind in sc_inds_list])
                    if normalize:
                        baseline_all_values = np.array([results_dict[gn][pl_baseline][metric_name][sc_ind]
                                                        for sc_ind in sc_inds_list])
                    else:
                        baseline_all_values = np.ones_like(yi_all_values)

                    yi_all_values_norm = yi_all_values / baseline_all_values
                    planner_y_values_list.append(yi_all_values_norm.mean())
                    planner_y_errors_list.append(yi_all_values_norm.std())

                planner_y_errors_list = np.array(planner_y_errors_list)
                planner_y_values_list = np.array(planner_y_values_list)
                if type(plt_config['marker']) == dict:
                    marker = plt_config['marker'][pl_name_full]
                else:
                    marker = plt_config['marker']

                axes[row_ind][col_ind].plot(x_values_list, planner_y_values_list, marker=marker,
                                            linewidth=plt_config['linewidth'], markersize=plt_config['markersize'],
                                            label=pl_name_short)
                axes[row_ind][col_ind].fill_between(x_values_list, planner_y_values_list - planner_y_errors_list,
                                                    planner_y_values_list + planner_y_errors_list,
                                                    alpha=plt_config['alpha'])
                per_metric_ymins[col_ind] = min(per_metric_ymins[col_ind],
                                                np.min(planner_y_values_list - planner_y_errors_list))
                per_metric_ymaxs[col_ind] = max(per_metric_ymaxs[col_ind],
                                                np.max(planner_y_values_list + planner_y_errors_list))

    for col_ind, metric_name in enumerate(metrics_to_plot):
        y_diff = (per_metric_ymaxs[col_ind] - per_metric_ymins[col_ind])
        for row_ind, ax in enumerate(axes[:, col_ind]):
            if y_label_per_metric is not None:
                ax.set_ylabel(y_label_per_metric[col_ind])
            if y_lim_per_metric is not None:
                ax.set_ylim(y_lim_per_metric[col_ind])
            else:
                ax.set_ylim(per_metric_ymins[col_ind] - y_diff / 10, per_metric_ymaxs[col_ind] + y_diff / 6)
            x_mean = np.mean(ax.get_xlim())
            if plt_config['group_by_size'] > 0:
                ax.text(x_mean, per_metric_ymaxs[col_ind] + y_diff / 12,
                        '%s=%s%s' % (group_by_name, group_by_values_unique[row_ind], group_by_units),
                        size=plt_config['group_by_size'], ha='center',
                        bbox=dict(boxstyle="round", ec=(1., .5, 0.5), fc=(1., .8, .8), ))

        title = metric_name
        if metrics_normalize[col_ind]:
            title = title + ' normalized'
        _ = axes[0, col_ind].set_title(title)
        _ = axes[-1, col_ind].set_xlabel(plot_by_name)
    _ = axes[-1, -1].legend(bbox_to_anchor=plt_config['bbox_to_anchor'], shadow=False, frameon=True,
                            framealpha=0.35)
    if save:
        fig.savefig(path_to_project + '/figures/' + name + '.png', dpi=fig.dpi)
