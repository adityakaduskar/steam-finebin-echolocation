| agent | seeds | greedy coverage | greedy collisions/ep | sampled coverage | sampled collisions/ep |
|---|---|---|---|---|---|
| range + learned beam | 3 | 27.7 ± 1.4 | 15.4 ± 2.0 | 30.9 ± 1.6 | 27.3 ± 5.7 |
| range + scripted scan | 3 | 30.4 ± 0.3 | 24.4 ± 3.3 | 31.8 ± 0.7 | 37.6 ± 4.5 |
| range + fixed ahead beam | 3 | 32.0 ± 3.2 | 29.3 ± 11.5 | 33.3 ± 1.1 | 42.1 ± 12.2 |
| range + omni click | 3 | 28.5 ± 8.1 | 29.3 ± 14.4 | 31.2 ± 3.4 | 42.9 ± 15.7 |
| sonar image (queue 6 reference) | 3 | 37.0 ± 1.5 | 17.5 ± 6.7 | 38.4 ± 0.8 | 26.4 ± 7.4 |
| blind (queue 6 reference) | 3 | 24.5 ± 3.9 | 20.6 ± 5.3 | 27.8 ± 1.4 | 31.3 ± 4.6 |
| bump-and-turn heuristic | | 27.8 | 31.9 | | |

(mean over the 4 held-out buildings per seed; ± = standard deviation across seeds)
