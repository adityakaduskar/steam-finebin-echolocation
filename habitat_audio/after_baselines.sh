#!/bin/bash
# wait for the no-penalty baselines, launch the echo run with the collision penalty, then evaluate/plot the baselines
R=~/steamaudio/habitat_audio/runs
until grep -q "^done" $R/ppo_echo_pointgoal/train.log && grep -q "^done" $R/ppo_blind_pointgoal/train.log; do sleep 30; done
bash ~/steamaudio/habitat_audio/launch_train.sh habitat_audio/runs/ppo_echo_pointgoal_cp --task echo_pointgoal --collision-penalty 0.1 --steps 600000 --envs 8 --rollout 128 --seed 1
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
for r in ppo_echo_pointgoal ppo_blind_pointgoal; do python habitat_audio/plot_training.py $R/$r; python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 2>&1 | grep -E "success|Traceback" > $R/$r/eval_summary.txt; done
echo BASELINE-EVAL-DONE > $R/baselines_done.flag
