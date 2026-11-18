# Learning log

My study guide for this project: concepts, decisions and why I made them.

## Milestone 1 — Game engine + random player

Status: code written and tests passing; quiz and sign-off still to do.

### Concepts
- Game engine: the single source of truth for the rules (legal moves, gravity, wins, draws). MCTS calls it thousands of times per move, so a rules bug would silently poison all the self-play data.
- Canonical form: the board as seen by the player to move. My pieces are +1, the opponent's are -1, whichever player I am. It equals `board * current_player`. The network only sees this version, so it learns each pattern once instead of once per player, and its value output always means "good for whoever is about to move".
- Absolute vs canonical board: absolute means player 1 is always +1 and player 2 is always -1. The two are identical on player 1's turn and sign-flipped on player 2's turn.
- Immutable states: `play()` returns a new position and leaves the old one alone, so each MCTS tree node can own its position safely.
- Last-move win check: a four in a row can only be created by the piece just placed, so only the four lines through that piece need checking. The check walks both ways along each line because the new piece can land in the middle of a line.
- Player as a function: a player is any function that takes a state and returns a column, which makes random, MCTS and network players interchangeable.

### Decisions (and why)
- Board representation: NumPy 6x7 array of +1/-1/0 vs bitboards → NumPy array, because it is readable and speed is out of scope for now.
- Where canonical form lives: store the absolute board plus `current_player` and compute the canonical view on request, vs always store the canonical board and flip after each move → absolute plus a method (went with Claude's recommendation: printing and debugging stay simple and the flip is one explicit line).
- Making a move: return a new state vs mutate in place with undo → new state, because it avoids shared-state bugs in MCTS for the cost of a 42-cell copy.
- Win detection: check lines through the last piece vs scan the whole board → last piece only.
- Row order: row 0 at the top vs at the bottom → row 0 at the bottom. My reasoning: it matches how I picture the board. It also makes a piece's row equal to its height, so gravity is "row = number of pieces already in the column". The cost is one `[::-1]` when printing.
- Turn after a winning move: the turn still passes, so in a won position `current_player` is the loser. Matters for the value sign in MCTS later.
- Environment: project-local `.venv` with `requirements.txt` (numpy, pytest).

### Quiz questions I should be able to answer
- Why does canonical form roughly halve what the network has to learn?
- In a position where player 1 has just won, what is `current_player`, and why will that matter for MCTS?
- Why is it enough to check only the lines through the last piece placed?
- Why does the win check walk in both directions along each line?
- Why does `play()` copy the board instead of changing it in place?

### Experiments I ran
- (none yet)

### Things I'm still fuzzy on
- Whose turn it is after a winning move. On the first quiz I said `current_player` is the winner and the value is +1. Correct answer: the turn always passes, so `current_player` is the loser and the position is worth -1 to the player to move. MCTS's sign flip on the way back up is what turns that into +1 for the player who made the winning move.
  - Quiz 2: got `winner` right and that player 2's pieces are -1, but still skipped the value. Remember: after player 2 wins, `current_player = +1`, and the value for the player to move is -1.
- What canonical form actually does. On quiz 2 I said it "checks for X's because that's the piece just placed". Correct answer: it is a relabeling where the player to move is always +1. "X to move with three in a row" and "O to move with three in a row" become the identical array, so the network learns the pattern once.
- Quiz 2 smaller gaps: the win check has to walk both ways along a line (`X X _ X` filled in the middle), and the concrete in-place `play()` bug is sibling MCTS nodes sharing one board, so trying move 4 from S still has move 3's piece on the board.
