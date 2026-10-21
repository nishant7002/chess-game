"""
tests/test_benchmarks.py
Unit tests verifying benchmark metric integrity and reproducible data collection.
"""

import os
import pandas as pd
from backend.benchmark import run_benchmarks, BENCHMARK_POSITIONS

def test_benchmark_runner_and_metrics():
    # Run short benchmark on endgame position at depth 1 and 2
    test_positions = {"Endgame": BENCHMARK_POSITIONS["Endgame"]}
    df = run_benchmarks(depths=[1, 2], positions=test_positions)

    assert not df.empty
    assert "runtime_ms" in df.columns
    assert "nodes_expanded" in df.columns
    assert "leaf_evaluations" in df.columns
    assert "pruned_branches" in df.columns

    # Verify Minimax and Alpha-Beta equivalence at depth 2
    mm_row = df[(df["algorithm"] == "Minimax") & (df["depth"] == 2)].iloc[0]
    ab_row = df[(df["algorithm"] == "Alpha-Beta") & (df["depth"] == 2)].iloc[0]

    assert mm_row["eval_score"] == ab_row["eval_score"]
    assert ab_row["leaf_evaluations"] < mm_row["leaf_evaluations"]
