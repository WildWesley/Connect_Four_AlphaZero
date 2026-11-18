"""Simple opponents to measure the AI against, plus a helper to play a game.

A "player" in this project is just a function: it takes a Connect4 state
and returns the column to play. That keeps random players, MCTS players
and network players interchangeable.
"""

import numpy as np

from game.connect4 import Connect4


def make_random_player(seed=None):
    """A player that picks uniformly among the legal columns."""
    rng = np.random.default_rng(seed)

    def choose_move(state):
        return int(rng.choice(state.legal_moves()))

    return choose_move


def play_game(player_1, player_2, verbose=False):
    """Play one full game. Returns +1 if player 1 won, -1 if player 2 won, 0 for a draw."""
    players = {1: player_1, -1: player_2}
    state = Connect4()
    while not state.is_over():
        col = players[state.current_player](state)
        state = state.play(col)
        if verbose:
            print(state, "\n")
    return state.winner if state.winner is not None else 0


if __name__ == "__main__":
    # Run with:  python -m eval.baselines
    result = play_game(make_random_player(), make_random_player(), verbose=True)
    print({1: "X (player 1) wins", -1: "O (player 2) wins", 0: "Draw"}[result])
