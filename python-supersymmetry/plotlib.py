import time

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches
from mpl_toolkits import mplot3d


import numpy as np


def init():
    mpl.style.use("seaborn")

def equal_axes():
    plt.axis("equal")
    plt.gca().set_aspect('equal', adjustable='box')

def magic(kwargss):
    do_show = kwargss.pop('show', False)
    for func, kwargs in kwargss.items():
        f = getattr(plt, func)
        if type(kwargs) is dict:
            getattr(plt, func)(**kwargs)
        else:
            getattr(plt, func)(kwargs)
    if do_show:
        plt.show()

def geom_plot(**kwargs):
    equal_axes()
    plt.xlabel("x")
    plt.ylabel("y")
    magic(kwargs)

def mkarrow(start, end, curved=False, **kwargs):
    alpha = kwargs.pop('alpha', 0.8)
    return patches.FancyArrowPatch(
        start,
        end,
        arrowstyle="Simple,tail_width=0.5,head_width=4,head_length=8",
        connectionstyle="arc3,rad=.2" if curved > 0 else "arc3,rad=-.2" if curved < 0 else None,
        alpha=alpha,
        **kwargs,
    )

def arrow(start, end, curved=False, text="", **kwargs):
    plt.gca().add_patch(mkarrow(start, end, curved, **kwargs))
    if text:
        plt.text(*end, text)

def compare_algorithms(algos, arg_gen, averagings=1, xfunc=None, **kwargs):
    init()
    times = {
        algo: []
        for algo
        in algos
    }
    x = []
    for arg in arg_gen:
        x.append(arg)
        for algo, func in algos.items():
            avgs = []
            for averaging in range(averagings):
                t0 = time.perf_counter()
                func(arg)
                t1 = time.perf_counter()
                avgs.append(t1 - t0)
            times[algo].append(np.mean(avgs))
    if xfunc is not None:
        x = [xfunc(xi) for xi in x]
    plt.figure()
    for algo, results in times.items():
        plt.plot(x, results)
    plt.legend(list(times))
    plt.xlabel("n")
    plt.ylabel("Computation time (seconds), average over {} runs".format(averagings))
    magic(kwargs)

def plot_vectors(vectors, ax, **kwargs):
    init()
    ax.plot3D(*zip(*vectors), alpha=0.6, linewidth=4);
    ax.scatter3D(*zip(*vectors), s=400);
    magic(kwargs)

def plot_path(vectors, transformer, text=True, **kwargs):
    init()
    if kwargs.pop('figure', True):
        plt.figure(figsize=(8,8))
    s = kwargs.pop('s', 100)
    plt.scatter(*transformer(np.array(vectors)).T, s=s)
    arrow(
        transformer(np.array(vectors[0])),
        transformer(np.array(vectors[0])),
        text=str(vectors[0]) if text else None,
        curved=True
    )
    for vector, prev_vector in zip(vectors[1:], vectors[:-1]):
        arrow(
            transformer(np.array(prev_vector)),
            transformer(np.array(vector)),
            text=str(vector) if text else None,
            curved=True
        )
    geom_plot(**kwargs);