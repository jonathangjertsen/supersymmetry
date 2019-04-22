from itertools import combinations

from matplotlib import pyplot as plt

from game import Game
from hooks import NoHooks

def populate_opponent_models(game, players, model_classes, model_params):
    m = len(players)
    
    assert m == len(model_classes), "{} players and {} model classes".format(m, len(model_classes))
    assert m == len(model_params), "{} players and {} model param dicts".format(m, len(model_params))
    
    for i in range(m):
        if not hasattr(players[i], 'opponent_models'):
            continue
        assert len(players[i].opponent_models) == 0
        
        for j in range(1, m):
            k = (i + j) % m
            model = model_classes[k](players[k].name, game, model_params[k])
            players[i].opponent_models.append(model)

class Simulator(object):
    def __init__(
        self,
        player_class,
        player_params=None,
        max_steps=50,
        n=4,
        hooks=None,
        player_colors = ("red","black",),
        opponent_classes=None,
        opponent_params=None,
    ):
        self.n = n
        self.hooks = hooks if hooks else NoHooks()
        self.player_colors = player_colors
        self.player_class = player_class
        self.player_params = player_params
        self.max_steps = max_steps
        self.winners = []
        
        if opponent_classes:
            self.opponent_classes = opponent_classes
        else:
            self.opponent_classes = []
        
        if opponent_params:
            self.opponent_params = opponent_params
        else:
            self.opponent_params =  [{} for opponent_class in self.opponent_classes]
    
    def execute(self, n_sims):
        for run in range(n_sims):
            game = Game(self.player_colors, self.n)
            
            player_list = [
                self.player_class(color, game, self.player_params)
                for color in self.player_colors
            ]
            player_dict={
                player.name: player
                for player in player_list
            }
            if self.opponent_classes:
                populate_opponent_models(game, player_list, self.opponent_classes, self.opponent_params)
            winners_this_run = game.run(
                max_steps=self.max_steps,
                players=player_dict,
                hooks=self.hooks
            )
            self.winners.append(winners_this_run)

class ResultPlotter(object):
    def __init__(self, simulator):
        self.simulator = simulator
    
    def get_dists(self):
        return {
            color: [
                steps
                for step_winners
                in self.simulator.winners
                for color_, steps
                in step_winners
                if color_ == color
            ]
            for color in self.simulator.player_colors
        }
    
    def plot_distributions(self):
        plt.figure(figsize=(7, 7))
        dists = self.get_dists()
        for color, dist in dists.items():
            plt.hist(
                dist, 
                alpha=0.8,
                color=color,
                bins=15
            )
        plt.xlabel("Number of moves")
        plt.ylabel("Density")
        plt.title("Distribution of game lengths")
        plt.show()
    
    def plot_correlations(self):
        dists = self.get_dists()
        for color_x, color_y in combinations(self.simulator.player_colors, 2):
            plt.figure(figsize=(7, 7))
            dist_x = dists[color_x]
            dist_y = dists[color_y]
            min_ = min(*dist_x, *dist_y)
            max_ = max(*dist_x, *dist_y)
            ties = [(x, y) for x, y in zip(dist_x, dist_y) if x == y]
            dist_x, dist_y = [x for x, y in zip(dist_x, dist_y) if x != y], [y for x, y in zip(dist_x, dist_y) if x != y]
            colors = [color_x if x < y else color_y for x, y in zip(dist_x, dist_y)]

            plt.scatter(dist_x, dist_y, alpha=0.5, color=colors)
            if ties:
                plt.scatter(*zip(*ties), marker="x")
            plt.xlabel("#moves by {}".format(color_x))
            plt.ylabel("#moves by {}".format(color_y))
            plt.xlim(min_ - 1, max_ + 1)
            plt.ylim(min_ - 1, max_ + 1)
            plt.title("Matchup: {} vs. {}".format(color_x, color_y))
            plt.axis("equal")
            plt.show()
