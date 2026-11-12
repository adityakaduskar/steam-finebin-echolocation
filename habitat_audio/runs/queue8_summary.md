### A. Memory wipe (held-out office_2 + hotel_0, greedy, 30 episodes each; mean ± s.d. over 3 seeds)

| agent | memory kept | wiped every 20 steps | wiped every step (no memory) |
|---|---|---|---|
| sonar image | 25.4 ± 0.8 cells, 22.7 ± 9.5 coll | 27.5 ± 1.0 cells, 20.8 ± 8.6 coll | 20.9 ± 2.4 cells, 71.4 ± 6.9 coll |
| sonar + learned beam | 23.3 ± 3.7 cells, 15.1 ± 4.3 coll | 23.9 ± 1.8 cells, 17.9 ± 4.3 coll | 16.3 ± 2.8 cells, 89.3 ± 15.5 coll |
| range + learned beam | 21.8 ± 1.5 cells, 16.9 ± 3.2 coll | 24.2 ± 1.8 cells, 18.1 ± 2.8 coll | 22.8 ± 1.8 cells, 78.6 ± 8.0 coll |
| blind | 21.3 ± 3.2 cells, 22.2 ± 6.1 coll | 18.2 ± 2.4 cells, 17.6 ± 2.1 coll | 3.2 ± 0.0 cells, 1.0 ± 0.0 coll |

### B. Click-cost sweep, range + learned beam (held-out 4 buildings, greedy; mean ± s.d. over 3 seeds)

| click cost | coverage (cells) | collisions / episode | clicks / step |
|---|---|---|---|
| 0.01 (queue 7) | 27.7 ± 1.4 | 15.4 ± 2.0 | 0.70 (0.38, 0.96, 0.76) |
