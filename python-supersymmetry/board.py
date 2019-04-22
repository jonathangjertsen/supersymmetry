import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from coordinate_transformer import CoordinateTransformer
import plotlib

class Board():
    def __init__(self, n=4, colors = ("red", "yellow", "green", "black", "blue", "grey")):
        self.n = n
        
        # A transformation that rotates the board by 60 degrees.
        rotator = CoordinateTransformer(
            transform = np.array([
                [0, -1, 0],
                [0, 0,  1],
                [1, 0,  0]
            ])
        )
        
        # A function that determines whether the coordinate belongs to the home of color 0.
        # Inferred from looking at the coordinates on the board.
        def in_first_home(vec):
            return vec[0] > n and vec[1] >= -n and vec[2] <= n

        # Mapping from color to a function that determines whether the coordinate belongs to its home.
        self.colors = {
            colors[0]: in_first_home,
            colors[1]: lambda vec: in_first_home(rotator.transform(vec, +1)),
            colors[2]: lambda vec: in_first_home(rotator.transform(vec, +2)),
            colors[3]: lambda vec: in_first_home(rotator.transform(vec, +3)),
            colors[4]: lambda vec: in_first_home(rotator.transform(vec, -2)),
            colors[5]: lambda vec: in_first_home(rotator.transform(vec, -1)),
        }
    
        # Mapping from color to a function that measures game progress.
        self.progress_function = {
            colors[0]: lambda vec: - vec[0] + vec[1] - vec[2],
            colors[1]: lambda vec: - vec[0] - vec[1] - vec[2],
            colors[2]: lambda vec: + vec[0] - vec[1] - vec[2],
            colors[3]: lambda vec: + vec[0] - vec[1] + vec[2],
            colors[5]: lambda vec: + vec[0] + vec[1] + vec[2],
            colors[4]: lambda vec: - vec[0] - vec[1] + vec[2],
        }

        # Mapping from color to the color of the opposing player.
        self.opposing = {
            colors[0]: colors[3],
            colors[1]: colors[4],
            colors[2]: colors[5],
        }
        for a, b in self.opposing.copy().items():
            self.opposing[b] = a
        
        # All vectors that may possibly be on the board
        hex_vectors = self.hexgrid()
        
        # All vectors in the central field
        self.field_spots = list(map(tuple, filter(self.in_field, hex_vectors)))
        
        # All vectors in each home
        self.color_spots = {
            color: list(map(tuple, filter(func, hex_vectors)))
            for color, func in self.colors.items()
        }
        
        # All vectors in 
        self.board_spots = self.field_spots.copy()
        for spots in self.color_spots.values():
            self.board_spots.extend(spots)
    
    def in_board(self, vec):
        """Returns whether the vector is inside of the board"""
        if self.in_field(vec):
            return True
        for func in self.colors.values():
            if func(vec, self.n):
                return True
        return False

    def in_field(self, vec):
        """Returns whether the vector is inside of the central field"""
        return (abs(vec[0]) + abs(vec[1]) + abs(vec[2])) <= 2 * self.n
    
    def hexgrid(self):
        """Returns a list of vectors that may or may not be inside of the board."""
        n = self.n * 2
        vectors = []
        for u in range(-n, n+1):
            us = [u] * (2*n+1)
            if u < 0:
                vectors.extend(zip(us, range(-n-u, n+1), range(-n, n+u+1)))
            else:
                vectors.extend(zip(us, range(-n, n-u+1), range(-n+u, n+1)))
        return vectors


class BoardPlotter(object):
    def __init__(self, board, transformer):
        self.board = board
        self.transformer = transformer
    
    def plot_transformed(self, in_vectors, newfig=True, text=False, **kwargs):
        mpl.style.use("default")
        if newfig:
            plt.figure(figsize=(7, 7))
        
        transformed = self.transformer(np.array(in_vectors))
        
        if text:
            for (xh, yh, zh), (x, y) in zip(in_vectors, transformed):
                plt.text(x, y, "[{},{},{}]".format(xh, yh, zh), fontsize=7)
        
        if len(transformed) > 0:
            alpha = kwargs.pop('alpha', 0.3)
            plt.scatter(*transformed.T, alpha=alpha, **kwargs)
        plotlib.geom_plot(xticks=[], yticks=[], xlabel="", ylabel="")
    
    def plot_spots(self, text=False, **kwargs):
        newfig = kwargs.pop('newfig', False)
        self.show_spots(self.board.field_spots, newfig=newfig, color="lightgreen", text=text, **kwargs)
        for color, spots in self.board.color_spots.items():
            self.show_spots(spots, newfig=False, color=color, text=text, **kwargs)
    
    def plot_move(self, vec_in, vec_out, curved=True, **kwargs):
        plotlib.arrow(self.transformer(vec_in), self.transformer(vec_out), curved, **kwargs)
    
    def show_spots(self, spots, **kwargs):
        self.plot_transformed(spots, **kwargs)
