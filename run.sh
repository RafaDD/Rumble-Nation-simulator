#!/bin/bash


echo "--- Running Stage 0 ---"
python buffer.py --stage 0 --round 200 --explore 1.0 --random_sim 1.0
for seed in {0..2}; do
    echo "Training Stage 0 with seed $seed"
    python train_offline.py --stage 0 --bs 256 --min 0.05 --max 0.95 --epochs 300 --seed "$seed"
done

for i in {1..8}; do
    echo "--- Running Stage $i ---"

    explore_val=""
    random_sim_val=""

    if (( i >= 1 && i <= 2 )); then
        explore_val="0.3"
        random_sim_val="0.2"
    elif (( i >= 3 && i <= 4 )); then
        explore_val="0.15"
        random_sim_val="0.2"
    elif (( i >= 5 && i <= 6 )); then
        explore_val="0.05"
        random_sim_val="0.15"
    elif (( i >= 7 && i <= 8 )); then
        explore_val="0.0"
        random_sim_val="0.1"
    fi

    python buffer.py --stage "$i" --round 60 --explore "$explore_val" --random_sim "$random_sim_val"

    for seed in {0..2}; do
        echo "Training Stage $i with seed $seed"
        python train_offline.py --stage "$i" --bs 128 --min 0.05 --max 0.95 --epochs 300 --seed "$seed"
    done
done

echo "--- Script Finished ---" 