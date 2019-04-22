import numpy as np
import pytest

from coordinate_transformer import CoordinateTransformer
from game import Game
from board import Board
from hex_grid_algorithms import grid_spiral, grid_brute_force, grid_fast, grid_redblob
from hooks import NoHooks, MultiHooks
from players import RandomPlayer, NonPlanningProgressMaximizer, PlanningProgressMaximizer, RandomSingleMovePlayer, SingleMoveProgressMaximizer
from simulator import Simulator
import plotlib
import plots


def transformer(matrix):
    return CoordinateTransformer(np.array(matrix))


def eq(a, b):
    return np.array_equal(a, b)


@pytest.fixture
def vectors():
    return ((1, 0), (0, 1), (1, 1), (-1, 1), (-1, -1), (2, -2), (3.0, -2.3))


def test_ct_id(vectors):
    trans = transformer([[1, 0], [0, 1]])

    for vec in vectors:
        assert eq(trans(vec), vec)
        assert eq(trans(vec, 2), vec)
        assert eq(trans(vec, -1), vec)
        assert eq(trans(vec, 0), vec)


def test_ct_flip(vectors):
    trans = transformer([[0, 1], [1, 0]])

    for vec in vectors:
        assert eq(trans(vec), list(reversed(vec)))
        assert eq(trans(vec, -1), list(reversed(vec)))
        assert eq(trans(vec, 2), vec)


def test_can_create_game():
    game = Game(["red", "blue"])


def test_can_create_hooks():
    no_hooks = NoHooks()
    multi_hooks = MultiHooks(NoHooks(), NoHooks())


def test_can_create_player():
    players = ["red", "black", "green", "yellow", "blue", "grey"]
    game = Game(players)
    player = RandomPlayer(players[0], game)
    player = NonPlanningProgressMaximizer(players[1], game)
    player = PlanningProgressMaximizer(players[2], game, { 'max_depth': 5, })
    player = SingleMoveProgressMaximizer(players[3], game)
    player = RandomSingleMovePlayer(players[3], game)


def test_can_create_board():
    board = Board()
    board = Board(n=8)


def test_hex_algorithms():
    assert grid_fast(4) == [(-4, 0, -4), (-4, 1, -3), (-4, 2, -2), (-4, 3, -1), (-4, 4, 0), (-3, -1, -4), (-3, 0, -3), (-3, 1, -2), (-3, 2, -1), (-3, 3, 0), (-3, 4, 1), (-2, -2, -4), (-2, -1, -3), (-2, 0, -2), (-2, 1, -1), (-2, 2, 0), (-2, 3, 1), (-2, 4, 2), (-1, -3, -4), (-1, -2, -3), (-1, -1, -2), (-1, 0, -1), (-1, 1, 0), (-1, 2, 1), (-1, 3, 2), (-1, 4, 3), (0, -4, -4), (0, -3, -3), (0, -2, -2), (0, -1, -1), (0, 0, 0), (0, 1, 1), (0, 2, 2), (0, 3, 3), (0, 4, 4), (1, -4, -3), (1, -3, -2), (1, -2, -1), (1, -1, 0), (1, 0, 1), (1, 1, 2), (1, 2, 3), (1, 3, 4), (2, -4, -2), (2, -3, -1), (2, -2, 0), (2, -1, 1), (2, 0, 2), (2, 1, 3), (2, 2, 4), (3, -4, -1), (3, -3, 0), (3, -2, 1), (3, -1, 2), (3, 0, 3), (3, 1, 4), (4, -4, 0), (4, -3, 1), (4, -2, 2), (4, -1, 3), (4, 0, 4)]
    assert grid_spiral(4) == [(0, 0, 0), (1, 1, 0), (0, 1, 0), (0, 1, -1), (0, 0, -1), (1, 0, -1), (1, 0, 0), (2, 1, 0), (2, 2, 0), (1, 2, 0), (0, 2, 0), (0, 2, -1), (0, 2, -2), (0, 1, -2), (0, 0, -2), (1, 0, -2), (2, 0, -2), (2, 0, -1), (2, 0, 0), (3, 1, 0), (3, 2, 0), (3, 3, 0), (2, 3, 0), (1, 3, 0), (0, 3, 0), (0, 3, -1), (0, 3, -2), (0, 3, -3), (0, 2, -3), (0, 1, -3), (0, 0, -3), (1, 0, -3), (2, 0, -3), (3, 0, -3), (3, 0, -2), (3, 0, -1), (3, 0, 0), (4, 1, 0), (4, 2, 0), (4, 3, 0), (4, 4, 0), (3, 4, 0), (2, 4, 0), (1, 4, 0), (0, 4, 0), (0, 4, -1), (0, 4, -2), (0, 4, -3), (0, 4, -4), (0, 3, -4), (0, 2, -4), (0, 1, -4), (0, 0, -4), (1, 0, -4), (2, 0, -4), (3, 0, -4), (4, 0, -4), (4, 0, -3), (4, 0, -2), (4, 0, -1), (4, 0, 0)]

    for n in range(1, 10):
        spiral = grid_spiral(n)
        brute_force = grid_brute_force(n)
        redblob = grid_redblob(n)
        fast = grid_fast(n)
        assert brute_force == redblob
        assert brute_force == fast
        assert brute_force != spiral


def test_can_create_simulator():
    simulator = Simulator(RandomPlayer)
