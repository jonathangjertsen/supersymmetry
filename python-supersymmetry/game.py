from enum import Enum

import numpy as np

from board import Board, BoardPlotter

class InvalidMoveException(Exception):
    pass


class MoveState(Enum):
    FIRST = 0
    SUBSEQUENT = 1
    SUBSEQUENT_AFTER_SINGLE_MOVE = 2
    ALREADY_CHECKED = 3


class Game(object):
    TRUST_PLAYERS = False
    
    def __init__(self, players, n=4):
        self.board = Board(n)
        self.players = players
        self.player_spots = {
            color: spots.copy()
            for color, spots in self.board.color_spots.items()
            if color in players
        }
        self.cache_occupied = {}
        self.move_stack = []

    def get_line(self, vec_in, vec_out):
        """Find the line of coordinates from vec_in to vec_out.
        This code is currently the main hot path
        """
        for d, (xi, xo) in enumerate(zip(vec_in, vec_out)):
            # Search for a shared coordinate
            if xi != xo:
                continue

            # Next coordinate is not shared
            d2 = d + 1
            if d2 == 3:
                d2 = 0

            # Find the line from vec_in to vec_out
            line = np.array([spot for spot in self.board.board_spots if spot[d] == xi])

            # Sort it
            line_d2 = line[:, d2]
            line_d2_argsort = np.argsort(line_d2)
            line_d2 = line_d2[line_d2_argsort]
            line = line[line_d2_argsort]
            
            # Tricky
            vec_in_d2 = vec_in[d2]
            vec_out_d2 = vec_out[d2]
            mini_idx = min(vec_in_d2, vec_out_d2)
            maxi_idx = max(vec_in_d2, vec_out_d2)
            mini = np.argmax(line_d2 == mini_idx)
            maxi = np.argmax(line_d2 == maxi_idx)
            start = min(mini, maxi)
            stop = max(mini, maxi) + 1
            return line[start:stop]
    
    def occupied(self, spot):
        """Returns whether the spot is occupied"""
        if spot in self.cache_occupied:
            return self.cache_occupied[spot]
        else:
            for player, spots in self.player_spots.items():
                for spot_ in spots:
                    if spot == spot_:
                        self.cache_occupied[spot] = True
                        return True
        self.cache_occupied[spot] = False
        return False

    def occupation(self, line, vec_in):
        """Returns whether each spot in the line is occupied"""
        return [self.occupied(spot) and spot != vec_in for spot in line]
    
    def is_legal_move(self, player, vec_in, vec_out, move_state=MoveState.FIRST):
        """Returns whether vec_out is a legal place to stay in temporarily"""
        if move_state == MoveState.ALREADY_CHECKED and Game.TRUST_PLAYERS:
            return True, move_state
        
        # Cannot move after having made a single move
        if move_state == MoveState.SUBSEQUENT_AFTER_SINGLE_MOVE:
            return False, move_state
        
        # Cannot stop in an occupied spot
        if self.occupied(vec_out):
            return False, move_state
        
        # Look at the line from vec_in to vec_out
        line = self.get_line(vec_in, vec_out)
        
        # If there is no such line, we cannot stop there
        if line is None or len(line) == 0:
            return False, move_state
        
        # Special rule: 1-step moves need not be symmetric
        if move_state == MoveState.FIRST and len(line) == 2:
            return True, MoveState.SUBSEQUENT_AFTER_SINGLE_MOVE
        
        # Look at whether each spot in the line is occupied
        occupation = self.occupation(map(tuple, line), vec_in)
        
        # Line through position must be symmetric
        no_occupation = True
        len_ = len(occupation)
        for i in range((len_ + 1) // 2):
            occ, rocc = occupation[i], occupation[len_-i-1]
            if occ != rocc:
                return False, move_state
            if occ:
                no_occupation = False
        return (not no_occupation), MoveState.SUBSEQUENT
    
    def get_legal_moves(self, player, vec_in, move_state=MoveState.FIRST):
        """Gets all the legal moves in the board"""
        moves = []
        for vec_out in self.board.board_spots:
            legal, next_move_state = self.is_legal_move(player, vec_in, vec_out, move_state)
            if legal:
                moves.append((vec_out, next_move_state))
        return moves
    
    def is_legal_endpoint(self, player, vec_in, vec_out):
        """Returns whether vec_out is a legal place for a player piece to end up in"""
        # Can always end up in the same position
        if vec_in == vec_out:
            return True
        
        # Cannot end up in an occupied spot
        if self.occupied(vec_out):
            return False
        
        for color, spots in self.board.color_spots.items():
            if vec_out in spots:
                if color == player or color == self.board.opposing[player]:
                    return True
                return False
        
        # If the position is legal and in the field, we can end there
        if vec_out in self.board.field_spots:
            return True
        
        # Otherwise, we can not end there
        return False
    
    def do_move(self, player, vec_in, vec_out, move_state=MoveState.FIRST):
        if not self.is_legal_move(player, vec_in, vec_out, move_state):
            raise InvalidMoveException(player, vec_in, vec_out)
        for idx, spot in enumerate(self.player_spots[player]):
            if spot == vec_in:
                self.player_spots[player][idx] = vec_out
                self.cache_occupied[vec_in] = False
                self.cache_occupied[vec_out] = True
                return True
        return False
    
    def push_move(self, *args):
        self.move_stack.append(args)
        self.do_move(*args)
    
    def pop_move(self):
        player, vec_in, vec_out, move_state = self.move_stack.pop()
        self.do_move(player, vec_out, vec_in, MoveState.ALREADY_CHECKED)

    def win_condition(self, player):
        return all(spot in self.player_spots[player] for spot in self.board.color_spots[self.board.opposing[player]])
    
    @property
    def pieces_per_player(self):
        return (self.board.n * (self.board.n + 1)) // 2
    
    def run(self, max_steps, players, hooks):
        # Holds the winners in sorted order
        win_sequence = []

        # Callbacks that may be ran during the game
        pre_game_callback  = hooks.get('before_game', None)
        game_callback      = hooks.get('after_game', None)
        pre_move_callback  = hooks.get('before_move', None)
        move_callback      = hooks.get('after_move', None)
        pre_play_callback  = hooks.get('before_play', None)
        play_callback      = hooks.get('after_play', None)
        pre_round_callback = hooks.get('after_round', None)
        round_callback     = hooks.get('after_round', None)

        # Run pre-game callback
        if pre_game_callback:
            pre_game_callback(self)

        # Run until max steps is reached or all players have arrived
        for step in range(max_steps):
            # Run pre-round callback
            if pre_round_callback:
                pre_round_callback()

            # Let every player move
            winners_this_round = []
            for color, player in players.items():
                # Run pre-play callback
                if pre_play_callback:
                    pre_play_callback(color, player)

                # Let the player decide on a sequence of moves
                moves = player.play()

                # Run through them
                start = moves[0]
                for end in moves[1:]:
                    # Run pre-move callback
                    if pre_move_callback:
                        pre_move_callback(start, end)

                    # Perform the move
                    self.do_move(color, start, end)

                    # Run post-move callback
                    if move_callback:
                        move_callback(start, end)

                    # The start of the next move is the end of this move
                    start = end

                # Run post-play callback
                if play_callback:
                    play_callback(color, player, moves)

                # Check if the player has won
                if self.win_condition(color):
                    win_sequence.append((color, step))
                    winners_this_round.append(color)

            # If any players won this round, remove them from list of players
            if winners_this_round:
                # Eliminate the winners
                players = { color: player for color, player in players.items() if color not in winners_this_round }

                # The game ends when there are no more players
                if len(players) == 0:
                    if game_callback:
                        game_callback()
                    return win_sequence

            # Run post-round callback
            if round_callback:
                round_callback()        

        # Max steps reached
        if game_callback:
            game_callback()
        for color, player in players.items():
            win_sequence.append((color, max_steps))
        return win_sequence

class GamePlotter(object):
    def __init__(self, game, transformer):
        self.board_plotter = BoardPlotter(game.board, transformer)
        self.game = game
    
    def plot(self, text=False):
        self.board_plotter.plot_spots(text)
        for color, spots in self.game.player_spots.items():
            self.board_plotter.show_spots(spots, newfig=False, color=color, s=100)   
    
    def __getattr__(self, attr):
        return getattr(self.board_plotter, attr)