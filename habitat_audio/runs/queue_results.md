# Queue started Wed Nov  4 10:16:48 PM EST 2026

## ablation of ppo_echo_pointgoal
    Traceback (most recent call last):
    PPO greedy [echo zeros] success 0.15  SPL 0.11  mean length 176  collisions/episode 152.8
    PPO sample [echo zeros] success 0.33  SPL 0.25  mean length 133  collisions/episode 70.5

## ablation of ppo_echo_pointgoal_cp
    PPO greedy success 0.19  SPL 0.17  mean length 143  collisions/episode 15.7
    PPO sample success 0.21  SPL 0.19  mean length 40  collisions/episode 2.5

## ablation of ppo_echo_pointgoal (recovered rerun)
    PPO greedy success 0.15  SPL 0.11  mean length 177  collisions/episode 116.1
    PPO sample success 0.30  SPL 0.22  mean length 115  collisions/episode 37.2
    PPO greedy [echo shuffled] success 0.26  SPL 0.18  mean length 166  collisions/episode 91.1
    PPO sample [echo shuffled] success 0.27  SPL 0.20  mean length 138  collisions/episode 59.0
    PPO greedy [echo shuffled] success 0.31  SPL 0.29  mean length 137  collisions/episode 19.4
    PPO sample [echo shuffled] success 0.17  SPL 0.16  mean length 47  collisions/episode 5.3
    PPO greedy [echo zeros] success 0.19  SPL 0.17  mean length 155  collisions/episode 123.1
    PPO sample [echo zeros] success 0.23  SPL 0.22  mean length 109  collisions/episode 22.3

## penalty runs (600k, seed 1)
### ppo_echo_pointgoal_cp
    PPO greedy success 0.20  SPL 0.18  mean length 143  collisions/episode 16.0
    PPO sample success 0.17  SPL 0.16  mean length 39  collisions/episode 2.7
    random     success 0.01  SPL 0.01  mean length 23  collisions/episode 5.7
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### ppo_blind_pointgoal_cp
    Traceback (most recent call last):

## ppo_blind_pointgoal_cp (recovered rerun)
    PPO greedy success 0.24  SPL 0.24  mean length 41  collisions/episode 4.8
    PPO sample success 0.18  SPL 0.17  mean length 18  collisions/episode 1.4
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 6.2
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## head-scan echo + penalty, 600k, seed 1  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_echo_scan_cp, 586/586 steps 600064 episodes 53923)
    PPO greedy success 0.23  SPL 0.19  mean length 103  collisions/episode 17.5
    PPO sample success 0.24  SPL 0.21  mean length 31  collisions/episode 2.4
    random     success 0.03  SPL 0.02  mean length 24  collisions/episode 6.4
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## ablation of ppo_echo_scan_cp
    PPO greedy [echo shuffled] success 0.26  SPL 0.23  mean length 85  collisions/episode 38.8
    PPO sample [echo shuffled] success 0.17  SPL 0.16  mean length 36  collisions/episode 9.0
    PPO greedy [echo zeros] success 0.23  SPL 0.21  mean length 156  collisions/episode 134.2
    PPO sample [echo zeros] success 0.30  SPL 0.27  mean length 99  collisions/episode 52.6

## single-pose echo + penalty, 1.5M, seed 1  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_echo_cp_1p5M, 1465/1465 steps 1500160 episodes 60419)
    PPO greedy success 0.41  SPL 0.33  mean length 106  collisions/episode 39.1
    PPO sample success 0.44  SPL 0.38  mean length 53  collisions/episode 9.7
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 6.3
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## blind + penalty, 1.5M, seed 1  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_blind_cp_1p5M, 2930/2930 steps 1500160 episodes 104880)

## ablation of ppo_echo_cp_1p5M
    PPO greedy success 0.27  SPL 0.25  mean length 36  collisions/episode 3.5
    PPO sample success 0.20  SPL 0.19  mean length 21  collisions/episode 1.8
    random     success 0.01  SPL 0.01  mean length 24  collisions/episode 5.8
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
    PPO greedy [echo shuffled] success 0.26  SPL 0.23  mean length 78  collisions/episode 50.7
    PPO sample [echo shuffled] success 0.27  SPL 0.25  mean length 46  collisions/episode 19.5
    PPO greedy [echo zeros] success 0.22  SPL 0.21  mean length 151  collisions/episode 133.5
    PPO sample [echo zeros] success 0.25  SPL 0.22  mean length 76  collisions/episode 46.0

## head-scan echo + penalty, 1.5M, seed 1  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_echo_scan_cp_1p5M, 1465/1465 steps 1500160 episodes 55390)
    PPO greedy success 0.51  SPL 0.43  mean length 120  collisions/episode 55.4
    PPO sample success 0.64  SPL 0.49  mean length 87  collisions/episode 12.2
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 5.7
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## ablation of ppo_echo_scan_cp_1p5M
    PPO greedy [echo shuffled] success 0.40  SPL 0.32  mean length 147  collisions/episode 64.9
    PPO sample [echo shuffled] success 0.36  SPL 0.29  mean length 138  collisions/episode 50.5
    PPO greedy [echo zeros] success 0.24  SPL 0.21  mean length 162  collisions/episode 135.4
    PPO sample [echo zeros] success 0.37  SPL 0.33  mean length 139  collisions/episode 63.5

## single-pose echo + penalty, 600k, seed 2  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_echo_cp_seed2, 586/586 steps 600064 episodes 42590)
    PPO greedy success 0.35  SPL 0.27  mean length 137  collisions/episode 14.0
    PPO sample success 0.32  SPL 0.25  mean length 78  collisions/episode 8.0
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 5.9
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## blind + penalty, 600k, seed 2  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_blind_cp_seed2, 1172/1172 steps 600064 episodes 46973)
    PPO greedy success 0.01  SPL 0.01  mean length 51  collisions/episode 14.3
    PPO sample success 0.12  SPL 0.10  mean length 11  collisions/episode 0.9
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 6.0
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

## ablation of ppo_echo_cp_seed2
    PPO greedy [echo shuffled] success 0.35  SPL 0.27  mean length 148  collisions/episode 29.1
    PPO sample [echo shuffled] success 0.35  SPL 0.29  mean length 108  collisions/episode 20.3
    PPO greedy [echo zeros] success 0.35  SPL 0.31  mean length 138  collisions/episode 28.0
    PPO sample [echo zeros] success 0.32  SPL 0.28  mean length 113  collisions/episode 23.9

## head-scan echo + penalty, 600k, seed 2  (/home/adityakaduskar/steamaudio/habitat_audio/runs/ppo_echo_scan_cp_seed2, 586/586 steps 600064 episodes 25835)
    PPO greedy success 0.22  SPL 0.15  mean length 159  collisions/episode 62.9
    PPO sample success 0.27  SPL 0.22  mean length 53  collisions/episode 11.5
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 6.0
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0

# Queue finished Thu Nov  5 10:14:36 AM EST 2026

## ablation of ppo_echo_scan_cp_seed2
    PPO greedy [echo shuffled] success 0.23  SPL 0.17  mean length 168  collisions/episode 87.3
    PPO sample [echo shuffled] success 0.29  SPL 0.23  mean length 83  collisions/episode 27.1
    PPO greedy [echo zeros] success 0.21  SPL 0.15  mean length 169  collisions/episode 129.7
    PPO sample [echo zeros] success 0.24  SPL 0.18  mean length 114  collisions/episode 39.9
