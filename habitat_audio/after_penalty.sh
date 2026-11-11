#!/bin/bash
R=~/steamaudio/habitat_audio/runs
until grep -q "^done" $R/ppo_echo_pointgoal_cp/train.log && grep -q "^done" $R/ppo_blind_pointgoal_cp/train.log; do sleep 30; done
source ~/anaconda3/etc/profile.d/conda.sh && conda activate ss && cd ~/steamaudio
for r in ppo_echo_pointgoal_cp ppo_blind_pointgoal_cp; do python habitat_audio/plot_training.py $R/$r; python -m habitat_audio.ppo_eval --ckpt $R/$r/checkpoint.pt --episodes 100 2>&1 | grep -E "^PPO|^random|^oracle|Traceback" > $R/$r/eval_summary.txt; done
echo PENALTY-EVAL-DONE > $R/penalty_done.flag
