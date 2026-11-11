# Queue 3 started Fri Nov  6 12:37:39 AM EST 2026
CRASH in /home/adityakaduskar/steamaudio/habitat_audio/runs/q3_echo_scan_pointgoal_aux
# Queue 3b resumed Fri Nov  6 12:44:31 AM EST 2026 (stage-1 runs were already training)

## point-goal: blind, 3 scenes, 2M (early evaluation while the head-scan run trains)
### scene apartment_1 (train)
    PPO greedy success 0.29  SPL 0.29  mean length 101  collisions/episode 64.1
    PPO sample success 0.29  SPL 0.27  mean length 34  collisions/episode 7.3
    random     success 0.01  SPL 0.01  mean length 24  collisions/episode 6.0
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### scene van-gogh-room (train)
    PPO greedy success 0.85  SPL 0.84  mean length 36  collisions/episode 8.5
    PPO sample success 0.84  SPL 0.82  mean length 25  collisions/episode 2.0
    random     success 0.06  SPL 0.06  mean length 24  collisions/episode 7.5
    oracle     success 1.00  SPL 1.00  mean length 16  collisions/episode 0.0
### scene skokloster-castle (train)
    PPO greedy success 0.73  SPL 0.71  mean length 73  collisions/episode 14.6
    PPO sample success 0.67  SPL 0.63  mean length 51  collisions/episode 3.9
    random     success 0.03  SPL 0.02  mean length 23  collisions/episode 2.1
    oracle     success 0.99  SPL 0.99  mean length 30  collisions/episode 0.0
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.21  SPL 0.21  mean length 90  collisions/episode 55.5
    PPO sample success 0.24  SPL 0.23  mean length 30  collisions/episode 6.4
    random     success 0.00  SPL 0.00  mean length 24  collisions/episode 6.9
    oracle     success 1.00  SPL 1.00  mean length 35  collisions/episode 0.0

## INTERIM point-goal: head-scan echo + aux, 3 scenes, checkpoint at 1.0M of 2M steps
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.36  SPL 0.28  mean length 144  collisions/episode 48.9
    PPO sample success 0.26  SPL 0.20  mean length 79  collisions/episode 16.8
### scene apartment_1 (train)
    PPO greedy success 0.38  SPL 0.32  mean length 106  collisions/episode 21.7
    PPO sample success 0.32  SPL 0.27  mean length 54  collisions/episode 6.5

## point-goal: head-scan echo + aux loss, 3 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q3_echo_scan_pointgoal_aux, 1954/1954 steps 2000896 episodes 55185)
### scene apartment_1 (train)
    PPO greedy success 0.35  SPL 0.32  mean length 91  collisions/episode 25.4
    PPO sample success 0.46  SPL 0.40  mean length 48  collisions/episode 4.4
    random     success 0.01  SPL 0.01  mean length 24  collisions/episode 5.9
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### scene van-gogh-room (train)
    PPO greedy success 0.93  SPL 0.92  mean length 35  collisions/episode 9.6
    PPO sample success 0.91  SPL 0.89  mean length 25  collisions/episode 1.2
    random     success 0.08  SPL 0.08  mean length 24  collisions/episode 7.4
    oracle     success 1.00  SPL 1.00  mean length 16  collisions/episode 0.0
### scene skokloster-castle (train)
    PPO greedy success 0.88  SPL 0.84  mean length 59  collisions/episode 5.7
    PPO sample success 0.88  SPL 0.83  mean length 54  collisions/episode 1.8
    random     success 0.03  SPL 0.02  mean length 25  collisions/episode 2.7
    oracle     success 0.99  SPL 0.99  mean length 30  collisions/episode 0.0
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.18  SPL 0.16  mean length 120  collisions/episode 21.4
    PPO sample success 0.21  SPL 0.17  mean length 49  collisions/episode 3.6
    random     success 0.00  SPL 0.00  mean length 24  collisions/episode 7.0
    oracle     success 1.00  SPL 1.00  mean length 35  collisions/episode 0.0
### held-out scene, echoes shuffled
    PPO greedy [echo shuffled] success 0.31  SPL 0.26  mean length 112  collisions/episode 23.5
    PPO sample [echo shuffled] success 0.23  SPL 0.18  mean length 45  collisions/episode 6.1
### held-out scene, echoes zeros
    PPO greedy [echo zeros] success 0.21  SPL 0.21  mean length 165  collisions/episode 141.0
    PPO sample [echo zeros] success 0.32  SPL 0.30  mean length 142  collisions/episode 49.8

## point-goal: blind, 3 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q3_blind_pointgoal, 3907/3907 steps 2000384 episodes 81107)
### scene apartment_1 (train)
    PPO greedy success 0.29  SPL 0.29  mean length 101  collisions/episode 64.1
    PPO sample success 0.22  SPL 0.21  mean length 33  collisions/episode 7.0
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 6.5
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### scene van-gogh-room (train)
    PPO greedy success 0.85  SPL 0.84  mean length 36  collisions/episode 8.5
    PPO sample success 0.83  SPL 0.80  mean length 24  collisions/episode 1.5
    random     success 0.07  SPL 0.06  mean length 24  collisions/episode 7.0
    oracle     success 1.00  SPL 1.00  mean length 16  collisions/episode 0.0
### scene skokloster-castle (train)
    PPO greedy success 0.73  SPL 0.71  mean length 73  collisions/episode 14.6
    PPO sample success 0.65  SPL 0.61  mean length 51  collisions/episode 3.7
    random     success 0.04  SPL 0.04  mean length 24  collisions/episode 2.1
    oracle     success 0.99  SPL 0.99  mean length 30  collisions/episode 0.0
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.21  SPL 0.21  mean length 90  collisions/episode 55.5
    PPO sample success 0.21  SPL 0.21  mean length 31  collisions/episode 6.7
    random     success 0.00  SPL 0.00  mean length 24  collisions/episode 6.8
    oracle     success 1.00  SPL 1.00  mean length 35  collisions/episode 0.0

## explore: blind, 3 scenes, 2M (early evaluation while the head-scan explorer trains)
### scene apartment_1 (train)
    PPO greedy coverage 34.7 cells (8.7 m^2)  path 25.1 m  collisions/episode 23.9  collisions/m 0.95
    PPO sample coverage 34.6 cells (8.7 m^2)  path 24.1 m  collisions/episode 57.7  collisions/m 2.40
    random     coverage 9.6 cells (2.4 m^2)  path 4.1 m  collisions/episode 138.3  collisions/m 33.69
    bump-turn  coverage 47.0 cells (11.8 m^2)  path 31.6 m  collisions/episode 26.1  collisions/m 0.83
### scene van-gogh-room (train)
    PPO greedy coverage 28.5 cells (7.1 m^2)  path 24.0 m  collisions/episode 24.6  collisions/m 1.03
    PPO sample coverage 26.5 cells (6.6 m^2)  path 22.4 m  collisions/episode 58.4  collisions/m 2.61
    random     coverage 7.1 cells (1.8 m^2)  path 3.0 m  collisions/episode 139.6  collisions/m 45.95
    bump-turn  coverage 30.5 cells (7.6 m^2)  path 27.6 m  collisions/episode 28.4  collisions/m 1.03
### scene skokloster-castle (train)
    PPO greedy coverage 93.7 cells (23.4 m^2)  path 47.7 m  collisions/episode 11.5  collisions/m 0.24
    PPO sample coverage 90.1 cells (22.5 m^2)  path 44.2 m  collisions/episode 30.9  collisions/m 0.70
    random     coverage 16.7 cells (4.2 m^2)  path 7.1 m  collisions/episode 121.0  collisions/m 17.00
    bump-turn  coverage 95.3 cells (23.8 m^2)  path 49.3 m  collisions/episode 15.6  collisions/m 0.32
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy coverage 26.3 cells (6.6 m^2)  path 22.1 m  collisions/episode 26.3  collisions/m 1.19
    PPO sample coverage 26.1 cells (6.5 m^2)  path 20.4 m  collisions/episode 60.6  collisions/m 2.97
    random     coverage 9.1 cells (2.3 m^2)  path 3.9 m  collisions/episode 133.6  collisions/m 34.60
    bump-turn  coverage 31.3 cells (7.8 m^2)  path 24.6 m  collisions/episode 30.1  collisions/m 1.22

## INTERIM explore: head-scan echo + aux, 3 scenes, checkpoint at 1.0M of 2M steps
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy coverage 16.6 cells (4.2 m^2)  path 12.3 m  collisions/episode 16.7  collisions/m 1.36
    PPO sample coverage 26.4 cells (6.6 m^2)  path 19.4 m  collisions/episode 23.7  collisions/m 1.22
### scene apartment_1 (train)
    PPO greedy coverage 39.1 cells (9.8 m^2)  path 28.2 m  collisions/episode 9.9  collisions/m 0.35
    PPO sample coverage 41.4 cells (10.3 m^2)  path 28.3 m  collisions/episode 17.9  collisions/m 0.63

# Queue 3c resumed Fri Nov  6 02:14:08 PM EST 2026 after reboot (GPU back)

## explore: head-scan echo + aux loss, 3 scenes, 2M (resumed after reboot)  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q3_echo_scan_explore_aux, 1954/1954 steps 2000896 episodes 1032)
### scene apartment_1 (train)
    PPO greedy coverage 38.8 cells (9.7 m^2)  path 21.9 m  collisions/episode 7.8  collisions/m 0.36
    PPO sample coverage 43.2 cells (10.8 m^2)  path 24.9 m  collisions/episode 17.1  collisions/m 0.69
    random     coverage 9.9 cells (2.5 m^2)  path 4.1 m  collisions/episode 133.0  collisions/m 32.33
    bump-turn  coverage 43.6 cells (10.9 m^2)  path 30.5 m  collisions/episode 26.3  collisions/m 0.86
### scene van-gogh-room (train)
    PPO greedy coverage 30.3 cells (7.6 m^2)  path 28.2 m  collisions/episode 8.3  collisions/m 0.30
    PPO sample coverage 32.3 cells (8.1 m^2)  path 27.0 m  collisions/episode 19.9  collisions/m 0.73
    random     coverage 6.5 cells (1.6 m^2)  path 2.6 m  collisions/episode 143.3  collisions/m 56.14
    bump-turn  coverage 30.0 cells (7.5 m^2)  path 26.9 m  collisions/episode 29.3  collisions/m 1.09
### scene skokloster-castle (train)
    PPO greedy coverage 121.8 cells (30.4 m^2)  path 58.6 m  collisions/episode 1.6  collisions/m 0.03
    PPO sample coverage 119.0 cells (29.8 m^2)  path 57.4 m  collisions/episode 1.1  collisions/m 0.02
    random     coverage 19.5 cells (4.9 m^2)  path 8.5 m  collisions/episode 115.1  collisions/m 13.56
    bump-turn  coverage 94.2 cells (23.6 m^2)  path 47.3 m  collisions/episode 17.1  collisions/m 0.36
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy coverage 12.6 cells (3.2 m^2)  path 8.7 m  collisions/episode 13.2  collisions/m 1.53
    PPO sample coverage 16.4 cells (4.1 m^2)  path 14.4 m  collisions/episode 20.6  collisions/m 1.43
    random     coverage 8.0 cells (2.0 m^2)  path 3.2 m  collisions/episode 136.1  collisions/m 42.79
    bump-turn  coverage 32.6 cells (8.2 m^2)  path 23.9 m  collisions/episode 30.6  collisions/m 1.28
### held-out scene, echoes shuffled
    PPO greedy [echo shuffled] coverage 20.4 cells (5.1 m^2)  path 14.7 m  collisions/episode 15.8  collisions/m 1.08
    PPO sample [echo shuffled] coverage 22.9 cells (5.7 m^2)  path 16.8 m  collisions/episode 24.6  collisions/m 1.46
### held-out scene, echoes zeros
    PPO greedy [echo zeros] coverage 29.1 cells (7.3 m^2)  path 24.0 m  collisions/episode 39.4  collisions/m 1.64
    PPO sample [echo zeros] coverage 25.7 cells (6.4 m^2)  path 20.9 m  collisions/episode 53.4  collisions/m 2.55

## INTERIM point-goal: single-pose echo + aux, 3 scenes, checkpoint at ~1.1M of 2M steps
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.32  SPL 0.27  mean length 160  collisions/episode 27.0
    PPO sample success 0.23  SPL 0.18  mean length 111  collisions/episode 16.8
### scene apartment_1 (train)
    PPO greedy success 0.34  SPL 0.30  mean length 144  collisions/episode 35.0
    PPO sample success 0.39  SPL 0.31  mean length 89  collisions/episode 13.2

## point-goal: single-pose echo + aux loss, 3 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q3_echo_pointgoal_aux, 1954/1954 steps 2000896 episodes 61460)
### scene apartment_1 (train)
    PPO greedy success 0.27  SPL 0.26  mean length 55  collisions/episode 32.9
    PPO sample success 0.28  SPL 0.26  mean length 33  collisions/episode 6.8
    random     success 0.04  SPL 0.03  mean length 24  collisions/episode 5.2
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### scene van-gogh-room (train)
    PPO greedy success 0.94  SPL 0.93  mean length 29  collisions/episode 10.0
    PPO sample success 0.96  SPL 0.95  mean length 21  collisions/episode 0.8
    random     success 0.08  SPL 0.07  mean length 24  collisions/episode 7.1
    oracle     success 1.00  SPL 1.00  mean length 16  collisions/episode 0.0
### scene skokloster-castle (train)
    PPO greedy success 0.82  SPL 0.82  mean length 39  collisions/episode 9.3
    PPO sample success 0.83  SPL 0.82  mean length 37  collisions/episode 2.4
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 2.1
    oracle     success 0.99  SPL 0.99  mean length 30  collisions/episode 0.0
### scene 17DRP5sb8fy (HELD OUT)
    PPO greedy success 0.21  SPL 0.19  mean length 61  collisions/episode 39.0
    PPO sample success 0.18  SPL 0.17  mean length 31  collisions/episode 8.3
    random     success 0.00  SPL 0.00  mean length 24  collisions/episode 7.2
    oracle     success 1.00  SPL 1.00  mean length 35  collisions/episode 0.0
### held-out scene, echoes shuffled
    PPO greedy [echo shuffled] success 0.17  SPL 0.16  mean length 25  collisions/episode 7.4
    PPO sample [echo shuffled] success 0.16  SPL 0.15  mean length 21  collisions/episode 4.1
### held-out scene, echoes zeros
    PPO greedy [echo zeros] success 0.17  SPL 0.17  mean length 141  collisions/episode 121.6
    PPO sample [echo zeros] success 0.20  SPL 0.20  mean length 84  collisions/episode 38.6

# Queue 3 finished Fri Nov  6 07:10:48 PM EST 2026
