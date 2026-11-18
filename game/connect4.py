"""Connect Four rules: the board, legal moves, dropping pieces, wins and draws.

Conventions used everywhere in this project:

* The board is a 6x7 NumPy array. 0 = empty, +1 = player 1, -1 = player 2.
* Row 0 is the BOTTOM row, so a piece's row index is its height in the column.
* A state is never modified after it is created. play() returns a new state.
"""

import numpy as np

ROWS = 6
COLS = 7
WIN_LENGTH = 4

# The four line directions through a piece, as (row step, column step).
# We only need one of each opposite pair (e.g. "right" but not "left"),
# because the win check walks both ways along each direction.
DIRECTIONS = [
    (0, 1),   # horizontal
    (1, 0),   # vertical
    (1, 1),   # diagonal going up and to the right
    (1, -1),  # diagonal going up and to the left
]


class Connect4:
    """One position in a game of Connect Four."""

    def __init__(self, board=None, current_player=1, winner=None):
        if board is None:
            board = np.zeros((ROWS, COLS), dtype=np.int8)
        self.board = board
        # +1 or -1: whose turn it is to move in this position.
        self.current_player = current_player
        # +1 or -1 once somebody has four in a row, otherwise None.
        self.winner = winner

    # ----- questions about the position -----

    def legal_moves(self):
        """Columns that still have room. Empty once the game is over."""
        if self.winner is not None:
            return []
        # A column is full exactly when its top cell is occupied.
        top_row = self.board[ROWS - 1]
        return [col for col in range(COLS) if top_row[col] == 0]

    def is_draw(self):
        """The board is full and nobody won."""
        return self.winner is None and not np.any(self.board == 0)

    def is_over(self):
        return self.winner is not None or self.is_draw()

    def canonical_board(self):
        """The board from the point of view of the player to move.

        The player to move is always +1 and their opponent is always -1.
        The network only ever sees this version, so it learns each pattern
        once instead of once per player.

        Multiplying by current_player does it: if player 1 (+1) is to move
        nothing changes; if player 2 (-1) is to move every sign flips.
        """
        return self.board * self.current_player

    # ----- making a move -----

    def play(self, col):
        """Drop the current player's piece into `col`. Returns a NEW state."""
        if self.is_over():
            raise ValueError("The game is already over.")
        if not 0 <= col < COLS:
            raise ValueError(f"Column {col} is not on the board.")

        # Gravity: because row 0 is the bottom, the piece lands at a row
        # equal to the number of pieces already in the column.
        row = int(np.count_nonzero(self.board[:, col]))
        if row == ROWS:
            raise ValueError(f"Column {col} is full.")

        # Copy so the old state is untouched. MCTS relies on this: every
        # tree node keeps its own position, and exploring one branch can
        # never corrupt another.
        new_board = self.board.copy()
        new_board[row, col] = self.current_player

        # Only the piece just placed can have created a four in a row,
        # so that is the only piece we need to check.
        won = _makes_four(new_board, row, col)
        winner = self.current_player if won else None

        # The turn always passes, even after a winning move. So in a won
        # position, current_player is the LOSER. This matters later for
        # the value sign in MCTS.
        return Connect4(new_board, -self.current_player, winner)

    # ----- display -----

    def __str__(self):
        symbols = {1: "X", -1: "O", 0: "."}
        # Row 0 is the bottom, so print the rows in reverse to show the
        # board the right way up.
        lines = [
            " ".join(symbols[int(cell)] for cell in row)
            for row in self.board[::-1]
        ]
        lines.append(" ".join(str(col) for col in range(COLS)))
        return "\n".join(lines)


def _makes_four(board, row, col):
    """Is the piece at (row, col) part of a line of four or more?"""
    player = board[row, col]
    for d_row, d_col in DIRECTIONS:
        # Count the piece itself, then matching pieces on both sides of it.
        # Walking both ways matters: the new piece may land in the MIDDLE
        # of a line (X X _ X -> X X X X), not just at its end.
        length = (
            1
            + _count_in_direction(board, row, col, d_row, d_col, player)
            + _count_in_direction(board, row, col, -d_row, -d_col, player)
        )
        if length >= WIN_LENGTH:
            return True
    return False


def _count_in_direction(board, row, col, d_row, d_col, player):
    """Count consecutive `player` pieces starting one step away from (row, col)."""
    count = 0
    r, c = row + d_row, col + d_col
    while 0 <= r < ROWS and 0 <= c < COLS and board[r, c] == player:
        count += 1
        r += d_row
        c += d_col
    return count
