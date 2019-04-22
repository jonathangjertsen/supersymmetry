import matplotlib as mpl
from matplotlib import pyplot as plt
import numpy as np
import networkx as nx

from plotlib import arrow, geom_plot, init


def unit_coords_plot():
    init()
    u = np.array([1, 0])
    v = np.array([-1/2, np.sqrt(3)/2])
    w = np.array([1/2, np.sqrt(3)/2])

    plt.figure()
    arrow([0, 0], u, text="Au = (1, 0)", color="red")
    arrow([0, 0], v, text="Av = (-1/2, √3/2)", color="red")
    arrow([0, 0], w, text="Aw = (1/2, √3/2)", color="red")
    geom_plot()


def coordinate_plot(transformer):
    init()
    u = np.array([1, 0, 0])
    v = np.array([0, 1, 0])
    w = np.array([0, 0, 1])
    y = (v+w)/np.sqrt(3)

    plt.figure()
    arrow([0, 0], transformer(u), text="x = Au", color="red")
    arrow([0, 0], transformer(v), text="Av", color="red")
    arrow([0, 0], transformer(w), text="Aw = A(u + w)", color="red")
    arrow([0, 0], transformer(y), text="y = A(v + w)/√3")
    arrow(transformer(u), transformer(w))
    geom_plot()


def rotation_plot(rotator, transformer):
    init()
    u = np.array([1, 0, 0])
    v = np.array([0, 1, 0])
    w = np.array([0, 0, 1])
    
    u_ = rotator(u)
    v_ = rotator(v)
    w_ = rotator(w)

    alpha = 0.6
    
    plt.figure()
    arrow([0, 0], transformer(u), color="red", text="Au = RAw", alpha=alpha)
    arrow([0, 0], transformer(v), color="green", text="Av = -RAu", alpha=alpha)
    arrow([0, 0], transformer(w), color="blue", text="Aw = RAv", alpha=alpha)
    arrow([0, 0], transformer(u_), color="red", alpha=alpha)
    arrow([0, 0], transformer(v_), color="green", alpha=alpha)
    arrow([0, 0], transformer(w_), color="blue", alpha=alpha)
    arrow(transformer(u), transformer(u_), color="red", curved=-1, alpha=alpha)
    arrow(transformer(v), transformer(v_), color="green", curved=-1, alpha=alpha)
    arrow(transformer(w), transformer(w_), color="blue", curved=-1, alpha=alpha)
    geom_plot()


def progress_plot(board_plotter):
    n = board_plotter.board.n
    plt.figure(figsize=(9,9))
    board_plotter.plot_spots(newfig=False)
    board_plotter.plot_move(np.array([-2*n, n, -n]), np.array([2*n, -n, n]), text="Black: P = u−v+w")
    board_plotter.plot_move(np.array([2*n, -n, n]), np.array([-2*n, n, -n]), text="Red: P = −u+v−w")
    board_plotter.plot_move(np.array([-n, 2*n, n]), np.array([n, -2*n, -n]), text="Green: P = u−v−w")
    board_plotter.plot_move(np.array([n, -2*n, -n]), np.array([-n, 2*n, n]), text="Grey: P = −u+v+w")
    board_plotter.plot_move(np.array([-n, -n, -2*n]), np.array([n, n, 2*n]), text="Blue: P = −u−v−w")
    board_plotter.plot_move(np.array([n, n, 2*n]), np.array([-n, -n, -2*n]), text="Yellow: P = u+v+w")
    plt.ylim(-3.2*n, 3.3*n)
    plt.xlim(-3.3*n, 4.8*n);


def plot_move_tree(move_tree, board, name):
    plt.figure()
    nx.draw(
        move_tree,
        pos=nx.circular_layout(move_tree),
        node_size=[(board.progress_function[name](node) + 2 * board.n + 1) **2 * 5 for node in move_tree.nodes],
        with_labels=True
    )
    plt.plot()


def progress_time_plot(progress):
    mpl.style.use("seaborn")
    plt.figure()
    for game_progress in progress:
        for color, progression in game_progress.items():
            plt.plot(progression, color=color, alpha=0.5)
    plt.xlabel("Moves")
    plt.ylabel("Progress")
    plt.show()