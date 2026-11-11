# Queue 2 started Thu Nov  5 03:25:49 PM EST 2026

## explore: single-pose echo + bump sensor, 1M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/explore_echo, 977/977 steps 1000448 episodes 3328)
    PPO greedy coverage 39.5 cells (9.9 m^2)  path 23.9 m  collisions/episode 17.0  collisions/m 0.71
    PPO sample coverage 46.0 cells (11.5 m^2)  path 25.8 m  collisions/episode 25.2  collisions/m 0.98
    random     coverage 9.7 cells (2.4 m^2)  path 4.1 m  collisions/episode 133.5  collisions/m 32.60
    bump-turn  coverage 51.1 cells (12.8 m^2)  path 33.5 m  collisions/episode 25.0  collisions/m 0.75
    PPO greedy [echo shuffled] coverage 31.0 cells (7.8 m^2)  path 21.9 m  collisions/episode 24.1  collisions/m 1.10
    PPO sample [echo shuffled] coverage 33.4 cells (8.4 m^2)  path 21.6 m  collisions/episode 32.6  collisions/m 1.51
    PPO greedy [echo zeros] coverage 42.5 cells (10.6 m^2)  path 30.2 m  collisions/episode 25.4  collisions/m 0.84
    PPO sample [echo zeros] coverage 40.5 cells (10.1 m^2)  path 27.7 m  collisions/episode 35.3  collisions/m 1.27

## explore: blind (bump sensor only), 1M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/explore_blind, 1954/1954 steps 1000448 episodes 3332)
    PPO greedy coverage 54.1 cells (13.5 m^2)  path 36.8 m  collisions/episode 25.7  collisions/m 0.70
    PPO sample coverage 54.2 cells (13.6 m^2)  path 35.9 m  collisions/episode 31.6  collisions/m 0.88
    random     coverage 9.7 cells (2.4 m^2)  path 4.1 m  collisions/episode 134.4  collisions/m 32.49
    bump-turn  coverage 49.8 cells (12.5 m^2)  path 33.2 m  collisions/episode 24.8  collisions/m 0.74

## explore: head-scan echo + bump sensor, 1M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/explore_echo_scan, 977/977 steps 1000448 episodes 3328)
    EVAL FAILED (see eval_full.log)

## explore: head-scan echo + bump sensor, 1M (re-evaluation after loader fix)
    PPO greedy [echo shuffled] coverage 37.3 cells (9.3 m^2)  path 25.4 m  collisions/episode 51.9  collisions/m 2.04
    PPO sample [echo shuffled] coverage 36.3 cells (9.1 m^2)  path 25.2 m  collisions/episode 54.7  collisions/m 2.17
    PPO greedy coverage 48.7 cells (12.2 m^2)  path 34.9 m  collisions/episode 14.6  collisions/m 0.42
    PPO sample coverage 49.2 cells (12.3 m^2)  path 33.3 m  collisions/episode 17.1  collisions/m 0.51
    random     coverage 8.9 cells (2.2 m^2)  path 3.7 m  collisions/episode 136.4  collisions/m 37.03
    bump-turn  coverage 49.5 cells (12.4 m^2)  path 33.2 m  collisions/episode 25.0  collisions/m 0.75
    Traceback (most recent call last):
    PPO greedy [echo zeros] coverage 34.4 cells (8.6 m^2)  path 27.2 m  collisions/episode 43.3  collisions/m 1.59
    PPO sample [echo zeros] coverage 40.5 cells (10.1 m^2)  path 28.1 m  collisions/episode 48.3  collisions/m 1.72

## audio-goal, no sliding, no echoes, 1M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/audiogoal_nosliding, 977/977 steps 1000448 episodes 85037)
    EVAL FAILED (see eval_full.log)

## audio-goal, no sliding, no echoes, 1M (re-evaluation after lib-path fix)
    PPO greedy success 0.19  SPL 0.17  mean length 169  collisions/episode 0.8
    PPO sample success 0.39  SPL 0.34  mean length 86  collisions/episode 5.3
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 6.1
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## audio-goal, no sliding, + echoes, 1M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/echo_audiogoal_nosliding, 977/977 steps 1000448 episodes 62664)
    PPO greedy success 0.27  SPL 0.24  mean length 153  collisions/episode 5.3
    PPO sample success 0.35  SPL 0.33  mean length 58  collisions/episode 4.5
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 6.4
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
    PPO greedy [echo shuffled] success 0.29  SPL 0.26  mean length 151  collisions/episode 8.9
    PPO sample [echo shuffled] success 0.36  SPL 0.33  mean length 93  collisions/episode 9.8
    PPO greedy [echo zeros] success 0.31  SPL 0.30  mean length 136  collisions/episode 4.1
    PPO sample [echo zeros] success 0.35  SPL 0.32  mean length 120  collisions/episode 8.9

# Queue 2 finished Fri Nov  6 12:36:19 AM EST 2026
