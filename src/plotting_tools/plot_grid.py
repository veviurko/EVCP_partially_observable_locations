from igraph.drawing.text import TextDrawer
from igraph import Plot
import numpy as np
import igraph


def _make_graph(grid):
    cable_inds = [ind for ind, reg in enumerate(grid.loads_regions) if len(reg) > 1]
    color_factors = np.linspace(0.1, 3, len(cable_inds))
    graph = igraph.Graph()

    passive_color = 'black'
    gen_color = 'red'
    load_color = np.array((.3, .3, .8))
    for node_ind, node in enumerate(grid.nodes):
        reg_ind = [ind for ind, reg in enumerate(grid.loads_regions) if node_ind in reg][0]
        if node.type == 'load':
            c = load_color * color_factors[cable_inds.index(reg_ind)] if reg_ind in cable_inds else load_color
            c = tuple(np.clip(c, 0, 1))
            s = 8
            shape = 'rectangle'
            label_size = 10
        elif node.type == 'gen':
            c = gen_color
            s = 12
            shape = 'circle'
            label_size = 15
        else:
            c = passive_color
            s = 4
            shape = 'triangle-up'
            label_size = 0

        graph.add_vertex(str(node_ind), color=c, size=s, label=node.name, shape=shape, label_dist=2,
                         label_size=label_size, )

    for line in grid.lines:
        node_from_ind = grid.nodes.index(line.node_from)
        node_to_ind = grid.nodes.index(line.node_to)
        graph.add_edge(str(node_from_ind), str(node_to_ind), )
    return graph


def plot_grid(grid, title, bbox=(650, 650), margin=25, title_size=36, save=False,
              path_to_figures='/home/gr1/Projects/DC_project//figures/'):
    graph = _make_graph(grid)
    if save:
        igraph.plot(graph, path_to_figures + title + '.png')
    else:
        igraph.plot()
    return graph
