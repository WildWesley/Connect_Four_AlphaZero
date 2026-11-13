# Connect Four AlphaZero — Project Spec

> This file is read by Claude Code at the start of every session. It describes **what we're building** and, just as importantly, **how we work together**. Read the whole thing before doing anything.

---

## 1. Who I am and why this project exists

I'm Nate, a computer engineering senior at BYU starting as a software engineer at Adobe in May 2027. I'm heading toward ML engineering and ML infrastructure, and this is my first serious ML project.

This project has **two goals, and they are equally important**:

1. **Ship a polished portfolio piece:** an AlphaZero-style AI that teaches itself Connect Four through self-play, with charts and a live "Can you beat my AI?" web demo for GitHub and LinkedIn.
2. **Understand every part of it deeply.** I need to be able to explain and defend every design decision in an interview, and implement the core algorithms (especially MCTS) on a whiteboard.

**If speed and my understanding ever conflict, choose my understanding.**

---

## 2. How we work together (learning mode). Follow these rules every session.

### Before writing code for a milestone
1. **Explain the concept first** in plain language: what this piece does, why AlphaZero needs it, and how it connects to the rest of the system. Use a small concrete example where possible.
2. **Lay out the design decisions** for the milestone (e.g., network size, MCTS constants, data format). Give me the options and tradeoffs, recommend one, and **let me make the call**. Don't silently pick.
3. Wait for my go-ahead before writing the code.

### While writing code
- Write **simple, readable code** over clever or highly optimized code. Clarity first; we can optimize later if needed.
- Add comments that explain **why**, not just what, especially for anything math-heavy (UCB/PUCT formula, loss function, value sign flipping).
- Keep files small and focused. No unnecessary abstractions or frameworks.
- Work in **small steps**. Don't build multiple milestones at once.

### After writing code
1. **Walk me through the code** file by file, highlighting the most important lines and any non-obvious tricks.
2. **Quiz me** with 3–5 short questions about how it works and why. Mix conceptual ("why does MCTS need exploration?") and practical ("what happens if c_puct is 0?"). Give feedback on my answers.
3. **Suggest one small experiment** I can run myself to build intuition (change a parameter, predict the result, then check).
4. **Update `LEARNING.md`** (see §8) with the concepts covered and the decisions made, *including my reasoning*.
5. **Don't move to the next milestone** until I say I understand the current one.

### Special rule: I write the MCTS myself (Milestone 6)
After the full system works with Claude-written MCTS, I will **re-implement MCTS from scratch myself** without looking at the original. During that milestone, Claude should **not write MCTS code**. Only give hints, review my code, and run tests comparing my version against the reference.

### General
- If I ask "just do it," it's fine to move faster, but still do the walkthrough and log the decisions afterward.
- If something I propose is a bad idea, tell me directly and explain why.
- Prefer explaining with references to the real AlphaZero paper (Silver et al., 2017) where relevant, so I learn the actual terminology.

---

## 3. Tech stack

| Area | Choice |
|---|---|
| Language | Python 3.11+ |
| ML | PyTorch |
| Game logic | NumPy |
| Training compute | Local CPU for development; Google Colab or Kaggle GPU for real training runs |
| Experiment tracking | Simple CSV/JSON logs + matplotlib (no heavy tools unless needed) |
| Testing | pytest |
| Model export | ONNX |
| Web demo | Plain HTML/CSS/JS + `onnxruntime-web`, hosted on GitHub Pages |

All settings (simulations per move, learning rate, buffer size, etc.) go in **one config file** so experiments are easy.

---

## 4. Suggested repo structure (propose changes if you see a better layout)

```
connect4-alphazero/
├── CLAUDE.md            # this file
├── LEARNING.md          # my learning log (concepts, decisions, quiz notes)
├── README.md            # portfolio-facing write-up (I write the final version)
├── config.py            # all hyperparameters in one place
├── game/
│   └── connect4.py      # board, legal moves, win detection, canonical form
├── mcts/
│   ├── mcts.py          # reference MCTS (Claude)
│   └── my_mcts.py       # my from-scratch rewrite (Milestone 6)
├── model/
│   └── network.py       # policy + value network
├── training/
│   ├── self_play.py     # generate games
│   ├── train.py         # train the network
│   └── arena.py         # new model vs best model
├── eval/
│   ├── baselines.py     # random player, pure-MCTS player
│   ├── solver.py        # wrapper around a perfect Connect Four solver
│   └── plots.py         # charts for the README / LinkedIn
├── export/
│   └── to_onnx.py
├── web/                 # the browser demo
├── checkpoints/         # saved models (keep a few for the "evolution" slider)
└── tests/
```

---

## 5. Technical design (starting point — explain and confirm each with me before building)

### Game
- Standard 6 rows × 7 columns, gravity drops, 4 in a row wins (horizontal, vertical, diagonal), draw when the board is full.
- **Canonical form:** always present the board from the perspective of the player to move (current player's pieces = +1, opponent = −1). Explain why this halves what the network has to learn.

### Neural network
- **Input:** board encoded as planes (e.g., current player's pieces, opponent's pieces; optionally a "to-move" plane).
- **Body:** small residual CNN (start around 4–6 residual blocks, 64 channels; we'll tune).
- **Policy head:** 7 logits (one per column), illegal moves masked out.
- **Value head:** single scalar in [−1, 1] via tanh (expected outcome for the player to move).
- **Loss:** value MSE + policy cross-entropy against MCTS visit distributions + L2 regularization.

### MCTS (AlphaZero-style PUCT)
- Selection by PUCT: Q + c_puct · P · √N_parent / (1 + N_child).
- Leaf evaluation by the network (no random rollouts once the network exists).
- Backpropagation with the **sign flip** between players (explain this carefully — it's a classic bug).
- Dirichlet noise at the root during self-play for exploration.
- Temperature: sample moves proportionally to visit counts early in the game, then play greedily.

### Self-play and training
- Self-play generates (canonical board, MCTS visit distribution, final outcome) examples.
- **Data augmentation:** horizontal mirror (Connect Four is left-right symmetric) — explain why this is free data.
- Replay buffer of recent games; train in rounds.
- **Arena gating:** new model plays the current best; promote it only if it wins ≥ ~55%.

### Evaluation (this produces the portfolio charts)
- Win rate vs a **random player** and vs a **pure-MCTS player** (no network) over training.
- **% of moves matching a perfect solver** on a fixed set of test positions — Connect Four is solved, so this is an objective measure of strength. Propose solver options (e.g., integrating an existing open-source solver vs. writing a simpler alpha-beta solver) and check licenses before using third-party code.
- Training loss curves (policy and value).
- Saved checkpoints at several stages (e.g., gen 0, early, mid, final) for side-by-side games and the web demo's evolution slider.

---

## 6. Milestones

Each milestone ends with: tests passing → walkthrough → quiz → `LEARNING.md` updated → my sign-off.

| # | Milestone | Done when |
|---|---|---|
| 1 | **Game engine** + random player | Tests cover all win directions, draws, illegal moves, canonical form |
| 2 | **Pure MCTS** (random rollouts, no network) | Beats a random player ~100% of the time; I can explain UCT selection |
| 3 | **Neural network** (policy + value) | Forward pass works on batches; illegal-move masking tested |
| 4 | **AlphaZero MCTS** (network-guided PUCT) | Full pipeline runs end-to-end on CPU, even if weak |
| 5 | **Self-play training loop** + arena gating | Clear improvement across generations vs baselines; first real GPU run |
| 6 | **I rewrite MCTS from scratch** (Claude only hints/reviews) | My `my_mcts.py` passes the same tests and matches the reference's move choices on test positions |
| 7 | **Evaluation + charts** (solver accuracy, win rates, losses, early-vs-late games) | Publication-quality charts saved in `eval/` output |
| 8 | **Web demo** (ONNX + JS MCTS in browser) | Playable on GitHub Pages; shows move probabilities + "who's winning" meter; checkpoint slider |
| 9 | **README + LinkedIn post** (I write; Claude reviews) | README has GIF at top, demo link, charts, how-it-works section, honest note on AI-assisted development |

---

## 7. Portfolio deliverables (definition of done)

- **Live demo:** "Can you beat my AI?" on GitHub Pages, with:
  - The AI's move probabilities shown above each column as it thinks
  - A win-probability meter
  - A slider to play against earlier checkpoints (random → near-perfect)
- **README:** GIF at the top, live demo link, key charts, a clear "How it works" section (self-play, MCTS, network), results vs the perfect solver, and what I learned.
- **Honest attribution:** a short note that the project was built with Claude Code, and that I re-implemented MCTS myself.
- **Charts:** win rate over training, solver accuracy over training, loss curves.

---

## 8. `LEARNING.md` format

Keep this file updated after every milestone. It's my study guide for interviews.

```
## Milestone N — <name>
### Concepts
- <concept>: <1–3 sentence plain-English explanation>
### Decisions (and why)
- <decision>: <options considered> → <what we chose> because <my reasoning>
### Quiz questions I should be able to answer
- <question>
### Experiments I ran
- <what I changed> → <what I predicted> → <what happened>
### Things I'm still fuzzy on
- <topic>
```

---

## 9. Out of scope (for now)

- Distributed or multi-GPU training
- Heavy performance optimization before the system works
- Games other than Connect Four
- Paid hosting or backend servers (the demo must run fully in the browser)

## 10. First session

1. Read this whole file.
2. Give me a short overview of AlphaZero and how the pieces in §5 fit together — like a 5-minute lecture.
3. Propose any changes to the plan or repo structure.
4. Then start **Milestone 1** following the learning-mode rules in §2.
