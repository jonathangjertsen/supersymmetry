from collections import deque
import random
import networkx as nx

class Player(object):
    """Basic player with no defined behavious"""
    def __init__(self, name, game, params=None):
        self.name = name
        self.game = game
        self.params = params
    
    def __repr__(self):
        return "Player(name={}, class={}, {})".format(self.name, type(self).__name__, ", ".join("{}={}".format(key, value) for key, value in self.params.items()))
        
    def __str__(self):
        return repr(self)
        
    def total_progress(self):
        board = self.game.board
        spots = self.game.player_spots[self.name]
        return sum(board.progress_function[self.name](spot) for spot in spots)

    def positions(self):
        return self.game.player_spots[self.name]


class DepthFirstMoveFinderMixin(object):
    """Explores the entire tree of possibilities"""
    def __init__(self, name, game, params):
        super().__init__(name, game, params)
        self.explored_positions = deque([], maxlen=params.get('position_memory', 5))
    
    def moves(self):
        game = self.game
        board = self.game.board
        
        self.explored_positions.add(frozenset(self.positions()))
        
        for i in range(game.pieces_per_player):
            start_spot = game.player_spots[self.name][i]
            progress_before = board.progress_function[self.name](start_spot)
            
            move_tree = nx.DiGraph()
            move_tree.add_node(start_spot)
            
            self.explore(start_spot, move_tree, MoveState.FIRST, 1)
            for endpoint in move_tree.nodes():
                if endpoint != start_spot and game.is_legal_endpoint(self.name, start_spot, endpoint):
                    progress = board.progress_function[self.name](endpoint) - progress_before
                    path = list(self.path(start_spot, endpoint, move_tree))
                    yield progress, path

    def explore(self, start_spot, move_tree, move_state, depth):
        # Iterate over every legal move
        for move, next_move_state in self.game.get_legal_moves(self.name, start_spot, move_state):
            # Don't go in circles
            if move in move_tree.nodes:
                continue
            
            # Try the move
            self.game.push_move(self.name, start_spot, move, move_state)
            
            # See if we have seen this set of positions before.
            # If so, don't do the same thing again.
            position = frozenset(self.positions())
            if position in self.explored_positions:
                self.game.pop_move()
                continue
            
            # OK, this is new. Add the move to the tree
            move_tree.add_node(move)
            move_tree.add_edge(start_spot, move)
            
            # If we are at max depth, do not explore further
            if depth >= self.params['max_depth']:
                self.game.pop_move()
                continue
            
            # Go deeper
            self.explore(move, move_tree, next_move_state, depth + 1)
            self.game.pop_move()
    
    def path(self, start_spot, endpoint, move_tree):
        for path in nx.algorithms.simple_paths.all_simple_paths(move_tree, start_spot, endpoint):
            return path

class BaseProgressTracker(Player):
    def play(self):
        return self.choose(self.build_heap())
    
    def build_heap(self):
        heap = []
        for progress, move in self.moves():
            heapq.heappush(heap, (-progress, move))
        return heap

    def choose(self, heap):
        minus_max_progress, move = heapq.heappop(heap)
        max_pool = [move]
        max_pool_exhausted = False
        while not max_pool_exhausted:
            try:
                minus_progress, move = heapq.heappop(heap)
            except IndexError:
                break
            minus_progress = round(minus_progress, 2)
            if minus_progress != minus_max_progress:
                break
            max_pool.append(move)
        return random.choice(max_pool)

class NonPlanningProgressMaximizer(BaseProgressTracker, DepthFirstMoveFinderMixin):
    """Look ma, no code"""


class RandomSingleMovePlayer(Player):
    def play(self):
        game = player.game
        start_spot = game.player_spots[player.name][np.random.choice(game.pieces_per_player)]
        legal_moves = game.get_legal_moves(player.name, start_spot)
        while True:
            endpoint, move_state = random.choice(legal_moves)
            if game.is_legal_endpoint(player.name, start_spot, endpoint):
                return [start_spot, endpoint]


class RandomPlayer(Player, DepthFirstMoveFinderMixin):
    def play(self):
        return random.choice([move] for _, move in self.moves())


class SingleMoveProgressMaximizer(BaseProgressTracker):
    """Picks a sequence consisting of the single move that increases the score the most"""
    def moves(self):
        for i in range(self.game.pieces_per_player):
            yield from self.moves_for_piece(self.game.player_spots[self.name][i])

    def moves_for_piece(self, start_spot):
        game = self.game
        board = self.game.board
        progress_before = board.progress_function[self.name](start_spot)
        legal_moves = game.get_legal_moves(self.name, start_spot)
        for move, move_state in legal_moves:
            if game.is_legal_endpoint(self.name, start_spot, move):
                progress = board.progress_function[self.name](move) - progress_before
                yield progress, [start_spot, move]

class PlanningProgressMaximizer(BaseProgressTracker):
    def __init__(self, name, game, params):
        super().__init__(name, game, params)
        self.move_finder = NonPlanningProgressMaximizer(name, game, { 'max_depth': params['max_depth'] })
        self.opponent_models = params.get('opponent_models', [])

    def pop_n(self, n):
        for i in range(n):
            self.game.pop_move()
        
    def explore_consequences(self, depth, explored_positions, move=None):
        if depth == self.params['max_play_depth']:
            yield self.total_progress(), move
            return

        # Get the heap of moves
        heap = self.move_finder.build_heap()
        for i in range(min(self.params['fanout'], len(heap))):
            n_pushes = 0
            m_progress, play = heapq.heappop(heap)
            
            # At depth=0, we consider every move. At depth > 0, we only consider the top-level move
            if depth == 0:
                move = play
            
            # Only need to consider the start and end point
            start = play[0]
            end = play[-1]
            
            # Fake-play the move
            self.game.push_move(self.name, start, end, MoveState.ALREADY_CHECKED)
            n_pushes += 1
            
            # If this position has been explored already, don't explore further
            position = frozenset(self.positions())
            if position in explored_positions:
                self.pop_n(n_pushes)
                break
            explored_positions.add(position)
            
            # Let the opponents move
            for opponent in self.opponent_models:
                opponent_move = opponent.play()
                opponent_start = opponent_move[0]
                opponent_end = opponent_move[-1]
                self.game.push_move(self.name, start, end, MoveState.ALREADY_CHECKED)
                n_pushes += 1
            
            # Check the expected total progress after doing the move
            sum_progress = 0
            n_moves = 0
            for total_progress, _move in self.explore_consequences(depth + 1, explored_positions, move):
                sum_progress += total_progress
                n_moves += 1
            
            # If there were no possible moves, just continue
            if n_moves == 0:
                self.pop_n(n_pushes)
                continue
            
            # Yield the mean progress for the move
            yield sum_progress / n_moves, move
            self.pop_n(n_pushes)
    
    def moves(self):
        explored_positions = set()
        explored_positions.add(frozenset(self.positions()))
        for total_progress, move in self.explore_consequences(0, explored_positions):
            yield total_progress, move