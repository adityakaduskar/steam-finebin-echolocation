# Queue 4 (Replica) started Fri Nov  6 10:01:03 PM EST 2026

## INTERIM Replica point-goal: head-scan echo + aux, checkpoint_500000 on held-out office_2 and hotel_0 (50 episodes)
### replica/office_2 (HELD OUT)
    PPO greedy success 0.28  SPL 0.26  mean length 159  collisions/episode 14.8
    PPO sample success 0.24  SPL 0.23  mean length 65  collisions/episode 7.8
### replica/hotel_0 (HELD OUT)
    PPO greedy success 0.40  SPL 0.38  mean length 151  collisions/episode 9.5
    PPO sample success 0.26  SPL 0.24  mean length 45  collisions/episode 2.6
# Queue 4b (Replica, resumed after eval fix) started Sat Nov  7 02:44:44 AM EST 2026

## Replica point-goal: head-scan echo + aux, 14 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q4_echo_scan_pointgoal_aux, 1117/1117 steps 2001664 episodes 51699)
### replica/office_2 (HELD OUT)
    PPO greedy success 0.34  SPL 0.31  mean length 122  collisions/episode 6.1
    PPO sample success 0.39  SPL 0.33  mean length 72  collisions/episode 7.7
    random     success 0.05  SPL 0.04  mean length 25  collisions/episode 8.4
    oracle     success 1.00  SPL 1.00  mean length 25  collisions/episode 0.0
### replica/frl_apartment_4 (HELD OUT)
    PPO greedy success 0.43  SPL 0.38  mean length 130  collisions/episode 6.9
    PPO sample success 0.48  SPL 0.40  mean length 72  collisions/episode 6.0
    random     success 0.01  SPL 0.01  mean length 23  collisions/episode 6.7
    oracle     success 1.00  SPL 1.00  mean length 30  collisions/episode 0.0
### replica/hotel_0 (HELD OUT)
    PPO greedy success 0.37  SPL 0.30  mean length 85  collisions/episode 5.2
    PPO sample success 0.37  SPL 0.27  mean length 46  collisions/episode 3.4
    random     success 0.05  SPL 0.05  mean length 23  collisions/episode 8.1
    oracle     success 1.00  SPL 1.00  mean length 27  collisions/episode 0.1
### replica/room_2 (HELD OUT)
    PPO greedy success 0.39  SPL 0.35  mean length 136  collisions/episode 4.2
    PPO sample success 0.51  SPL 0.44  mean length 66  collisions/episode 4.7
    random     success 0.12  SPL 0.11  mean length 25  collisions/episode 7.6
    oracle     success 1.00  SPL 1.00  mean length 23  collisions/episode 0.0
### replica/apartment_0 (train)
    PPO greedy success 0.14  SPL 0.12  mean length 85  collisions/episode 2.2
    PPO sample success 0.20  SPL 0.17  mean length 41  collisions/episode 2.0
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 6.4
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### replica/office_0 (train)
    PPO greedy success 0.28  SPL 0.22  mean length 82  collisions/episode 3.3
    PPO sample success 0.30  SPL 0.23  mean length 39  collisions/episode 2.0
    random     success 0.08  SPL 0.07  mean length 24  collisions/episode 8.9
    EVAL FAILED
### replica/room_0 (train)
    PPO greedy success 0.29  SPL 0.26  mean length 119  collisions/episode 4.6
    PPO sample success 0.36  SPL 0.29  mean length 48  collisions/episode 3.7
    random     success 0.04  SPL 0.04  mean length 24  collisions/episode 7.5
    oracle     success 1.00  SPL 1.00  mean length 28  collisions/episode 0.0
### held-out office_2 + hotel_0, echoes shuffled
    PPO greedy [echo shuffled] success 0.42  SPL 0.37  mean length 112  collisions/episode 10.6
    PPO sample [echo shuffled] success 0.40  SPL 0.33  mean length 86  collisions/episode 9.4
    PPO greedy [echo shuffled] success 0.39  SPL 0.30  mean length 70  collisions/episode 8.8
    PPO sample [echo shuffled] success 0.26  SPL 0.18  mean length 48  collisions/episode 5.7
### held-out office_2 + hotel_0, echoes zeros
    PPO greedy [echo zeros] success 0.44  SPL 0.41  mean length 134  collisions/episode 9.6
    PPO sample [echo zeros] success 0.52  SPL 0.44  mean length 118  collisions/episode 12.7
    PPO greedy [echo zeros] success 0.38  SPL 0.35  mean length 141  collisions/episode 11.0
    PPO sample [echo zeros] success 0.44  SPL 0.38  mean length 100  collisions/episode 12.1
### interim checkpoint_500000.pt on held-out office_2 + hotel_0
    PPO greedy success 0.33  SPL 0.30  mean length 154  collisions/episode 15.2
    PPO sample success 0.26  SPL 0.25  mean length 49  collisions/episode 6.2
    PPO greedy success 0.42  SPL 0.40  mean length 144  collisions/episode 8.4
    PPO sample success 0.39  SPL 0.36  mean length 44  collisions/episode 2.7

## Replica point-goal: blind, 14 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q4_blind_pointgoal, 1117/1117 steps 2001664 episodes 104200)
### replica/office_2 (HELD OUT)
    PPO greedy success 0.39  SPL 0.38  mean length 62  collisions/episode 3.8
    PPO sample success 0.37  SPL 0.37  mean length 36  collisions/episode 3.4
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 7.9
    oracle     success 1.00  SPL 1.00  mean length 25  collisions/episode 0.0
### replica/frl_apartment_4 (HELD OUT)
    PPO greedy success 0.28  SPL 0.28  mean length 76  collisions/episode 3.0
    PPO sample success 0.27  SPL 0.26  mean length 35  collisions/episode 2.9
    random     success 0.01  SPL 0.01  mean length 24  collisions/episode 6.7
    oracle     success 1.00  SPL 1.00  mean length 30  collisions/episode 0.0
### replica/hotel_0 (HELD OUT)
    PPO greedy success 0.45  SPL 0.44  mean length 75  collisions/episode 3.0
    PPO sample success 0.41  SPL 0.40  mean length 36  collisions/episode 2.9
    random     success 0.09  SPL 0.08  mean length 24  collisions/episode 8.2
    oracle     success 1.00  SPL 1.00  mean length 27  collisions/episode 0.1
### replica/room_2 (HELD OUT)
    PPO greedy success 0.44  SPL 0.43  mean length 50  collisions/episode 4.0
    PPO sample success 0.40  SPL 0.39  mean length 37  collisions/episode 2.9
    random     success 0.09  SPL 0.08  mean length 24  collisions/episode 6.3
    oracle     success 1.00  SPL 1.00  mean length 23  collisions/episode 0.0
### replica/apartment_0 (train)
    PPO greedy success 0.20  SPL 0.20  mean length 103  collisions/episode 2.6
    PPO sample success 0.20  SPL 0.19  mean length 37  collisions/episode 3.1
    random     success 0.02  SPL 0.02  mean length 24  collisions/episode 6.4
    oracle     success 1.00  SPL 1.00  mean length 34  collisions/episode 0.0
### replica/office_0 (train)
    PPO greedy success 0.41  SPL 0.40  mean length 51  collisions/episode 4.1
    PPO sample success 0.40  SPL 0.39  mean length 35  collisions/episode 3.2
    random     success 0.06  SPL 0.05  mean length 24  collisions/episode 8.6
    oracle     success 0.95  SPL 0.95  mean length 26  collisions/episode 0.1
### replica/room_0 (train)
    PPO greedy success 0.29  SPL 0.29  mean length 68  collisions/episode 3.6
    PPO sample success 0.31  SPL 0.30  mean length 36  collisions/episode 3.2
    random     success 0.03  SPL 0.03  mean length 24  collisions/episode 7.2
    oracle     success 1.00  SPL 1.00  mean length 28  collisions/episode 0.0

## Replica explore: head-scan echo + aux, 14 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q4_echo_scan_explore_aux, 1117/1117 steps 2001664 episodes 6664)
### replica/office_2 (HELD OUT)
    PPO greedy coverage 12.4 cells (3.1 m^2)  path 8.9 m  collisions/episode 10.1  collisions/m 1.13
    PPO sample coverage 25.7 cells (6.4 m^2)  path 19.4 m  collisions/episode 21.5  collisions/m 1.11
    random     coverage 6.2 cells (1.5 m^2)  path 2.4 m  collisions/episode 141.5  collisions/m 58.39
    bump-turn  coverage 25.9 cells (6.5 m^2)  path 20.1 m  collisions/episode 32.9  collisions/m 1.64
### replica/frl_apartment_4 (HELD OUT)
    PPO greedy coverage 36.6 cells (9.2 m^2)  path 25.7 m  collisions/episode 10.0  collisions/m 0.39
    PPO sample coverage 39.3 cells (9.8 m^2)  path 28.4 m  collisions/episode 20.4  collisions/m 0.72
    random     coverage 7.6 cells (1.9 m^2)  path 3.1 m  collisions/episode 139.5  collisions/m 45.38
    bump-turn  coverage 31.4 cells (7.8 m^2)  path 23.3 m  collisions/episode 30.9  collisions/m 1.33
### replica/hotel_0 (HELD OUT)
    PPO greedy coverage 17.1 cells (4.3 m^2)  path 12.7 m  collisions/episode 8.7  collisions/m 0.69
    PPO sample coverage 25.3 cells (6.3 m^2)  path 19.9 m  collisions/episode 24.0  collisions/m 1.21
    random     coverage 5.5 cells (1.4 m^2)  path 2.1 m  collisions/episode 143.6  collisions/m 67.49
    bump-turn  coverage 22.6 cells (5.7 m^2)  path 19.5 m  collisions/episode 33.1  collisions/m 1.70
### replica/room_2 (HELD OUT)
    PPO greedy coverage 27.6 cells (6.9 m^2)  path 18.5 m  collisions/episode 5.8  collisions/m 0.32
    PPO sample coverage 37.5 cells (9.4 m^2)  path 25.4 m  collisions/episode 14.1  collisions/m 0.56
    random     coverage 7.3 cells (1.8 m^2)  path 3.0 m  collisions/episode 140.8  collisions/m 47.61
    bump-turn  coverage 32.6 cells (8.1 m^2)  path 25.1 m  collisions/episode 29.6  collisions/m 1.18
### replica/apartment_0 (train)
    PPO greedy coverage 19.8 cells (5.0 m^2)  path 13.9 m  collisions/episode 8.6  collisions/m 0.61
    PPO sample coverage 34.5 cells (8.6 m^2)  path 22.4 m  collisions/episode 18.8  collisions/m 0.84
    random     coverage 9.3 cells (2.3 m^2)  path 3.9 m  collisions/episode 135.6  collisions/m 34.83
    bump-turn  coverage 33.6 cells (8.4 m^2)  path 24.7 m  collisions/episode 30.4  collisions/m 1.23
### replica/office_0 (train)
    PPO greedy coverage 13.1 cells (3.3 m^2)  path 8.4 m  collisions/episode 7.8  collisions/m 0.93
    PPO sample coverage 21.1 cells (5.3 m^2)  path 17.9 m  collisions/episode 24.1  collisions/m 1.35
    random     coverage 4.5 cells (1.1 m^2)  path 1.7 m  collisions/episode 143.1  collisions/m 86.53
    bump-turn  coverage 21.8 cells (5.5 m^2)  path 20.0 m  collisions/episode 33.1  collisions/m 1.66
### replica/room_0 (train)
    PPO greedy coverage 15.1 cells (3.8 m^2)  path 12.6 m  collisions/episode 8.7  collisions/m 0.69
    PPO sample coverage 24.4 cells (6.1 m^2)  path 19.3 m  collisions/episode 21.2  collisions/m 1.10
    random     coverage 6.5 cells (1.6 m^2)  path 2.5 m  collisions/episode 142.6  collisions/m 56.44
    bump-turn  coverage 26.2 cells (6.5 m^2)  path 21.4 m  collisions/episode 32.3  collisions/m 1.50
### held-out office_2 + hotel_0, echoes shuffled
    PPO greedy [echo shuffled] coverage 16.0 cells (4.0 m^2)  path 11.5 m  collisions/episode 13.4  collisions/m 1.16
    PPO sample [echo shuffled] coverage 19.4 cells (4.8 m^2)  path 14.6 m  collisions/episode 26.6  collisions/m 1.82
    PPO greedy [echo shuffled] coverage 16.6 cells (4.2 m^2)  path 12.4 m  collisions/episode 20.0  collisions/m 1.61
    PPO sample [echo shuffled] coverage 21.1 cells (5.3 m^2)  path 16.2 m  collisions/episode 35.6  collisions/m 2.20
### held-out office_2 + hotel_0, echoes zeros
    PPO greedy [echo zeros] coverage 9.7 cells (2.4 m^2)  path 5.6 m  collisions/episode 6.7  collisions/m 1.20
    PPO sample [echo zeros] coverage 18.0 cells (4.5 m^2)  path 14.5 m  collisions/episode 16.4  collisions/m 1.13
    PPO greedy [echo zeros] coverage 9.0 cells (2.2 m^2)  path 5.1 m  collisions/episode 6.9  collisions/m 1.34
    PPO sample [echo zeros] coverage 15.8 cells (4.0 m^2)  path 12.6 m  collisions/episode 18.6  collisions/m 1.47
### interim checkpoint_500000.pt on held-out office_2 + hotel_0
    PPO greedy coverage 26.5 cells (6.6 m^2)  path 20.2 m  collisions/episode 30.6  collisions/m 1.51
    PPO sample coverage 27.6 cells (6.9 m^2)  path 20.6 m  collisions/episode 51.5  collisions/m 2.50
    PPO greedy coverage 21.3 cells (5.3 m^2)  path 21.5 m  collisions/episode 25.7  collisions/m 1.19
    PPO sample coverage 23.5 cells (5.9 m^2)  path 19.4 m  collisions/episode 51.1  collisions/m 2.63
### interim checkpoint_1000000.pt on held-out office_2 + hotel_0
    PPO greedy coverage 19.5 cells (4.9 m^2)  path 14.0 m  collisions/episode 15.4  collisions/m 1.10
    PPO sample coverage 24.7 cells (6.2 m^2)  path 20.5 m  collisions/episode 23.9  collisions/m 1.17
    PPO greedy coverage 17.2 cells (4.3 m^2)  path 14.8 m  collisions/episode 10.5  collisions/m 0.71
    PPO sample coverage 22.3 cells (5.6 m^2)  path 17.1 m  collisions/episode 24.2  collisions/m 1.42
### interim checkpoint_1500000.pt on held-out office_2 + hotel_0
    PPO greedy coverage 16.2 cells (4.0 m^2)  path 11.9 m  collisions/episode 17.7  collisions/m 1.49
    PPO sample coverage 22.6 cells (5.6 m^2)  path 16.2 m  collisions/episode 34.1  collisions/m 2.11
    PPO greedy coverage 19.7 cells (4.9 m^2)  path 14.0 m  collisions/episode 19.0  collisions/m 1.35
    PPO sample coverage 22.3 cells (5.6 m^2)  path 17.9 m  collisions/episode 32.2  collisions/m 1.80

## Replica explore: blind, 14 scenes, 2M  (/home/adityakaduskar/steamaudio/habitat_audio/runs/q4_blind_explore, 1117/1117 steps 2001664 episodes 6664)
### replica/office_2 (HELD OUT)
    PPO greedy coverage 19.9 cells (5.0 m^2)  path 20.1 m  collisions/episode 16.1  collisions/m 0.80
    PPO sample coverage 25.6 cells (6.4 m^2)  path 19.9 m  collisions/episode 24.9  collisions/m 1.25
    random     coverage 5.9 cells (1.5 m^2)  path 2.2 m  collisions/episode 139.6  collisions/m 64.60
    bump-turn  coverage 26.7 cells (6.7 m^2)  path 20.9 m  collisions/episode 32.2  collisions/m 1.54
### replica/frl_apartment_4 (HELD OUT)
    PPO greedy coverage 24.1 cells (6.0 m^2)  path 22.3 m  collisions/episode 16.2  collisions/m 0.73
    PPO sample coverage 34.6 cells (8.6 m^2)  path 24.2 m  collisions/episode 23.2  collisions/m 0.96
    random     coverage 7.9 cells (2.0 m^2)  path 3.4 m  collisions/episode 141.3  collisions/m 42.13
    bump-turn  coverage 34.0 cells (8.5 m^2)  path 25.8 m  collisions/episode 29.9  collisions/m 1.16
### replica/hotel_0 (HELD OUT)
    PPO greedy coverage 18.8 cells (4.7 m^2)  path 18.8 m  collisions/episode 17.3  collisions/m 0.92
    PPO sample coverage 20.6 cells (5.2 m^2)  path 19.1 m  collisions/episode 26.5  collisions/m 1.39
    random     coverage 6.2 cells (1.5 m^2)  path 2.4 m  collisions/episode 144.1  collisions/m 59.13
    bump-turn  coverage 22.7 cells (5.7 m^2)  path 18.8 m  collisions/episode 33.4  collisions/m 1.78
### replica/room_2 (HELD OUT)
    PPO greedy coverage 19.1 cells (4.8 m^2)  path 22.0 m  collisions/episode 15.5  collisions/m 0.71
    PPO sample coverage 30.4 cells (7.6 m^2)  path 22.6 m  collisions/episode 23.8  collisions/m 1.05
    random     coverage 6.9 cells (1.7 m^2)  path 3.1 m  collisions/episode 138.7  collisions/m 45.19
    bump-turn  coverage 31.3 cells (7.8 m^2)  path 24.9 m  collisions/episode 29.9  collisions/m 1.20
### replica/apartment_0 (train)
    PPO greedy coverage 28.7 cells (7.2 m^2)  path 22.8 m  collisions/episode 16.1  collisions/m 0.71
    PPO sample coverage 30.4 cells (7.6 m^2)  path 23.3 m  collisions/episode 24.1  collisions/m 1.03
    random     coverage 7.4 cells (1.8 m^2)  path 3.0 m  collisions/episode 139.2  collisions/m 46.43
    bump-turn  coverage 30.8 cells (7.7 m^2)  path 24.3 m  collisions/episode 30.8  collisions/m 1.26
### replica/office_0 (train)
    PPO greedy coverage 17.1 cells (4.3 m^2)  path 17.3 m  collisions/episode 17.1  collisions/m 0.99
    PPO sample coverage 19.8 cells (4.9 m^2)  path 17.6 m  collisions/episode 26.5  collisions/m 1.51
    random     coverage 5.3 cells (1.3 m^2)  path 1.9 m  collisions/episode 145.4  collisions/m 75.05
    bump-turn  coverage 20.2 cells (5.0 m^2)  path 18.9 m  collisions/episode 34.1  collisions/m 1.81
### replica/room_0 (train)
    PPO greedy coverage 22.4 cells (5.6 m^2)  path 19.5 m  collisions/episode 17.0  collisions/m 0.87
    PPO sample coverage 25.0 cells (6.2 m^2)  path 19.7 m  collisions/episode 25.7  collisions/m 1.30
    random     coverage 6.9 cells (1.7 m^2)  path 2.9 m  collisions/episode 140.2  collisions/m 49.19
    bump-turn  coverage 24.4 cells (6.1 m^2)  path 20.3 m  collisions/episode 32.9  collisions/m 1.62

# Queue 4 finished Sat Nov  7 10:45:06 AM EST 2026
