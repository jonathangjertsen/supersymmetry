class GameHooks(object):
    def get(self, callback_name, default=None):
        if hasattr(self, callback_name):
            return lambda *args, **kwargs: getattr(self, callback_name)(*args, **kwargs)
        else:
            return default


class NoHooks(GameHooks):
    def get(self, callback, default=None):
        return default


class MultiHooks(GameHooks):
    def __init__(self, *hooks):
        self.hooks = list(hooks)
    
    def add(self, hook):
        self.hooks.append(hook)
    
    def get(self, callback_name, default=None):
        hooks_with_callback = [hook for hook in self.hooks if hasattr(hook, callback_name)]
        if not hooks_with_callback:
            return default
        
        def callback(*args, **kwargs):
            for hook in hooks_with_callback:
                getattr(hook, callback_name)(*args, **kwargs)
        return callback


class ProgressTrackerHooks(GameHooks):
    def __init__(self):
        self.progress = []
        self.progress_for_this_game = defaultdict(list)
    
    def before_game(self, game):
        self.progress_for_this_game = defaultdict(list)
    
    def after_play(self, color, player, moves):
        self.progress_for_this_game[color].append(player.total_progress())
    
    def after_game(self):
        self.progress.append(self.progress_for_this_game)


class PlotHooks(GameHooks):
    def __init__(self,
                 transform=np.array([
                    [    1,            0 ],
                    [ -1/2, np.sqrt(3)/2 ],
                    [  1/2, np.sqrt(3)/2 ],
                 ]),
                 fig_format="hexgrid-figures/tree-{}.png",
                 save_fig=False):
        self.transform = transform
        self.save_fig = save_fig
        self.fig_format = fig_format

    def before_game(self, game):
        mpl.style.use("default")
        self.play_counter = 0
        
        self.plotter = GamePlotter(
            game,
            transformer=CoordinateTransformer(
                transform=np.array(self.transform)
            )
        )
        
        self.plotter.plot(text=True)
        self.xlim = plt.xlim()
        self.ylim = plt.ylim()
    
    def after_move(self, start, end):
        self.plotter.plot_move(start, end)

    def before_play(self, color, player):
        self.plotter.plot()
        
    def after_play(self, color, player, moves):
        self.play_counter += 1
        plt.xticks([])
        plt.yticks([])
        plt.xlim(self.xlim)
        plt.ylim(self.ylim)
        
        if self.save_fig:
            plt.savefig(self.fig_format.format(self.play_counter))
            plt.close()
        else:
            plt.show()