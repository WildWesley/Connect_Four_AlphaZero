"""Tests for the game engine. Run with:  pytest"""

import numpy as np
import pytest

from eval.baselines import make_random_player, play_game
from game.connect4 import COLS, ROWS, Connect4


def play_moves(moves):
    """Play a list of columns from the empty board and return the final state."""
    state = Connect4()
    for col in moves:
        state = state.play(col)
    return state


# A full game (found by random search) that fills all 42 cells with no winner.
DRAW_GAME = [5, 5, 5, 0, 5, 4, 4, 6, 6, 3, 5, 1, 3, 5, 2, 1, 2, 3, 0, 4, 1,
             4, 3, 0, 2, 2, 2, 1, 0, 0, 0, 2, 1, 6, 1, 3, 4, 4, 3, 6, 6, 6]


# ----- basics -----

def test_new_game_is_empty_and_player_1_moves_first():
    state = Connect4()
    assert not state.board.any()
    assert state.current_player == 1
    assert state.legal_moves() == list(range(COLS))
    assert not state.is_over()


def test_pieces_fall_to_the_lowest_empty_row():
    state = play_moves([3, 3, 3])
    # Row 0 is the bottom, so the three pieces sit at rows 0, 1, 2.
    assert list(state.board[:3, 3]) == [1, -1, 1]
    assert state.board[3, 3] == 0


def test_players_alternate():
    state = Connect4()
    assert state.current_player == 1
    state = state.play(0)
    assert state.current_player == -1
    state = state.play(0)
    assert state.current_player == 1


def test_play_does_not_change_the_original_state():
    before = Connect4()
    after = before.play(3)
    assert not before.board.any()
    assert before.current_player == 1
    assert after.board[0, 3] == 1


# ----- wins in every direction -----

def test_horizontal_win():
    # Player 1 plays columns 0-3 along the bottom; player 2 stacks on top.
    state = play_moves([0, 0, 1, 1, 2, 2, 3])
    assert state.winner == 1
    assert state.is_over()


def test_vertical_win():
    state = play_moves([0, 1, 0, 1, 0, 1, 0])
    assert state.winner == 1


def test_diagonal_up_right_win():
    # Player 1 ends with pieces at (0,0), (1,1), (2,2), (3,3).
    state = play_moves([0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3])
    assert state.winner == 1


def test_diagonal_up_left_win():
    # Mirror image of the test above: (0,6), (1,5), (2,4), (3,3).
    state = play_moves([6, 5, 5, 4, 4, 3, 4, 3, 3, 0, 3])
    assert state.winner == 1


def test_player_2_can_win():
    state = play_moves([0, 1, 0, 1, 0, 1, 6, 1])
    assert state.winner == -1


def test_win_by_filling_the_middle_of_a_line():
    # Player 1 has columns 0, 1 and 3 on the bottom row, then plays 2.
    # The winning piece is in the middle, so the check must look both ways.
    state = play_moves([0, 0, 1, 1, 3, 3, 2])
    assert state.winner == 1


def test_three_in_a_row_is_not_a_win():
    state = play_moves([0, 0, 1, 1, 2])
    assert state.winner is None
    assert not state.is_over()


def test_turn_passes_even_after_a_winning_move():
    # In a won position the player "to move" is the loser.
    state = play_moves([0, 1, 0, 1, 0, 1, 0])
    assert state.winner == 1
    assert state.current_player == -1


# ----- draws -----

def test_full_board_with_no_winner_is_a_draw():
    state = play_moves(DRAW_GAME)
    assert len(DRAW_GAME) == ROWS * COLS
    assert state.winner is None
    assert state.is_draw()
    assert state.is_over()
    assert state.legal_moves() == []


def test_game_in_progress_is_not_a_draw():
    assert not play_moves(DRAW_GAME[:-1]).is_draw()


# ----- illegal moves -----

def test_full_column_is_illegal():
    state = play_moves([0] * ROWS)
    assert 0 not in state.legal_moves()
    with pytest.raises(ValueError):
        state.play(0)


@pytest.mark.parametrize("col", [-1, COLS])
def test_column_off_the_board_is_illegal(col):
    with pytest.raises(ValueError):
        Connect4().play(col)


def test_cannot_play_after_the_game_is_over():
    state = play_moves([0, 1, 0, 1, 0, 1, 0])
    assert state.legal_moves() == []
    with pytest.raises(ValueError):
        state.play(3)


# ----- canonical form -----

def test_canonical_board_is_unchanged_when_player_1_is_to_move():
    state = play_moves([3, 4])
    assert state.current_player == 1
    assert np.array_equal(state.canonical_board(), state.board)


def test_canonical_board_is_flipped_when_player_2_is_to_move():
    state = play_moves([3])
    assert state.current_player == -1
    # Player 1's piece is the OPPONENT's piece from player 2's point of view.
    assert state.board[0, 3] == 1
    assert state.canonical_board()[0, 3] == -1


def test_canonical_board_does_not_modify_the_real_board():
    state = play_moves([3])
    state.canonical_board()
    assert state.board[0, 3] == 1


# ----- cross-check against a slow, obviously-correct win scan -----

def has_four_anywhere(board, player):
    """Brute force: try every cell as the start of a line in every direction."""
    for row in range(ROWS):
        for col in range(COLS):
            for d_row, d_col in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                cells = [(row + i * d_row, col + i * d_col) for i in range(4)]
                if all(0 <= r < ROWS and 0 <= c < COLS and board[r, c] == player
                       for r, c in cells):
                    return True
    return False


def test_fast_win_check_agrees_with_brute_force_on_random_games():
    rng = np.random.default_rng(0)
    for _ in range(300):
        state = Connect4()
        while not state.is_over():
            state = state.play(int(rng.choice(state.legal_moves())))
            for player in (1, -1):
                assert has_four_anywhere(state.board, player) == (state.winner == player)


# ----- random player -----

def test_random_games_always_finish_with_a_valid_result():
    player_1 = make_random_player(seed=1)
    player_2 = make_random_player(seed=2)
    results = [play_game(player_1, player_2) for _ in range(100)]
    assert set(results) <= {1, -1, 0}
    # Both sides should win at least sometimes when both play randomly.
    assert 1 in results and -1 in results
