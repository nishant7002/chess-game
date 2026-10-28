"""
backend/benchmark.py
Comprehensive Experimental Benchmarking Suite for Chess AI Engine.
Compares Minimax, Alpha-Beta Pruning, Move Ordering, and Baselines across
controlled chess positions (Opening, Tactical Middlegame, Positional Middlegame, Endgame).
Generates CSV results and high-resolution Matplotlib performance plots.
"""

import os
import sys
import time
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless plot generation
import matplotlib.pyplot as plt

from backend.ai.evaluation import evaluate_board
from backend.ai.baseline import RandomAgent, GreedyAgent
from backend.ai.minimax import find_best_move_minimax
from backend.ai.alpha_beta import find_best_move_alpha_beta

# 4 Standard Controlled Benchmark Positions
BENCHMARK_POSITIONS = {
    "Opening": chess.STARTING_FEN,
    "Middlegame_Tactical": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5",
    "Middlegame_Positional": "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPP3PP/R2QKB1R w KQ - 1 9",
    "Endgame": "8/8/4k3/8/8/4K3/4R3/8 w - - 0 1"
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmark_reports")

def run_benchmarks(depths: List[int] = [1, 2, 3], positions: Dict[str, str] = BENCHMARK_POSITIONS) -> pd.DataFrame:
    """Executes controlled benchmarks across algorithms, positions, and depths."""
    records: List[Dict[str, Any]] = []

    print("=" * 75)
    print("STARTING CHESS AI EXPERIMENTAL BENCHMARKS")
    print("=" * 75)

    for pos_name, fen in positions.items():
        print(f"\n[Evaluating Position: {pos_name}]")
        board = chess.Board(fen)

        # 1. Baseline: Random Agent
        rnd_res = RandomAgent.select_move(board)
        records.append({
            "position": pos_name,
            "algorithm": "Random",
            "depth": 0,
            "runtime_ms": rnd_res["metrics"]["runtime_ms"],
            "nodes_generated": rnd_res["metrics"]["nodes_generated"],
            "nodes_expanded": rnd_res["metrics"]["nodes_expanded"],
            "leaf_evaluations": rnd_res["metrics"]["leaf_evaluations"],
            "pruned_branches": 0,
            "best_move": rnd_res["move"],
            "eval_score": rnd_res["eval"]
        })

        # 2. Baseline: Greedy Agent (1-ply)
        grd_res = GreedyAgent.select_move(board)
        records.append({
            "position": pos_name,
            "algorithm": "Greedy",
            "depth": 1,
            "runtime_ms": grd_res["metrics"]["runtime_ms"],
            "nodes_generated": grd_res["metrics"]["nodes_generated"],
            "nodes_expanded": grd_res["metrics"]["nodes_expanded"],
            "leaf_evaluations": grd_res["metrics"]["leaf_evaluations"],
            "pruned_branches": 0,
            "best_move": grd_res["move"],
            "eval_score": grd_res["eval"]
        })

        # 3. Depth-Scaled Searches: Minimax vs Alpha-Beta vs Alpha-Beta + Move Ordering
        for d in depths:
            print(f"  > Benchmarking depth {d}...")

            # Pure Minimax
            mm_res = find_best_move_minimax(board, depth=d)
            records.append({
                "position": pos_name,
                "algorithm": "Minimax",
                "depth": d,
                "runtime_ms": mm_res["metrics"]["runtime_ms"],
                "nodes_generated": mm_res["metrics"]["nodes_generated"],
                "nodes_expanded": mm_res["metrics"]["nodes_expanded"],
                "leaf_evaluations": mm_res["metrics"]["leaf_evaluations"],
                "pruned_branches": 0,
                "best_move": mm_res["move"],
                "eval_score": mm_res["eval"]
            })

            # Alpha-Beta without move ordering
            ab_res = find_best_move_alpha_beta(board, depth=d, use_move_ordering=False)
            records.append({
                "position": pos_name,
                "algorithm": "Alpha-Beta",
                "depth": d,
                "runtime_ms": ab_res["metrics"]["runtime_ms"],
                "nodes_generated": ab_res["metrics"]["nodes_generated"],
                "nodes_expanded": ab_res["metrics"]["nodes_expanded"],
                "leaf_evaluations": ab_res["metrics"]["leaf_evaluations"],
                "pruned_branches": ab_res["metrics"]["pruned_branches"],
                "best_move": ab_res["move"],
                "eval_score": ab_res["eval"]
            })

            # Alpha-Beta with move ordering
            abo_res = find_best_move_alpha_beta(board, depth=d, use_move_ordering=True)
            records.append({
                "position": pos_name,
                "algorithm": "Alpha-Beta (Ordered)",
                "depth": d,
                "runtime_ms": abo_res["metrics"]["runtime_ms"],
                "nodes_generated": abo_res["metrics"]["nodes_generated"],
                "nodes_expanded": abo_res["metrics"]["nodes_expanded"],
                "leaf_evaluations": abo_res["metrics"]["leaf_evaluations"],
                "pruned_branches": abo_res["metrics"]["pruned_branches"],
                "best_move": abo_res["move"],
                "eval_score": abo_res["eval"]
            })

    df = pd.DataFrame(records)
    return df

def generate_visualizations(df: pd.DataFrame, output_dir: str):
    """Generates comparative scientific plots from benchmark metrics."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Depth vs. Runtime (Averaged across positions)
    plt.figure(figsize=(9, 5))
    search_algos = ["Minimax", "Alpha-Beta", "Alpha-Beta (Ordered)"]
    df_search = df[df["algorithm"].isin(search_algos)]

    for algo in search_algos:
        subset = df_search[df_search["algorithm"] == algo].groupby("depth")["runtime_ms"].mean()
        plt.plot(subset.index, subset.values, marker="o", linewidth=2.5, label=algo)

    plt.title("Search Depth vs. Execution Runtime (ms)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Search Depth (ply)", fontsize=12)
    plt.ylabel("Mean Runtime (ms)", fontsize=12)
    plt.yscale("log")
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.legend(frameon=True, fontsize=11)
    plt.tight_layout()
    runtime_plot_path = os.path.join(output_dir, "benchmark_depth_vs_runtime.png")
    plt.savefig(runtime_plot_path, dpi=300)
    plt.close()
    print(f"Saved plot: {runtime_plot_path}")

    # 2. Depth vs. Nodes Expanded (Log Scale)
    plt.figure(figsize=(9, 5))
    for algo in search_algos:
        subset = df_search[df_search["algorithm"] == algo].groupby("depth")["nodes_expanded"].mean()
        plt.plot(subset.index, subset.values, marker="s", linewidth=2.5, label=algo)

    plt.title("Search Depth vs. Nodes Expanded (Log Scale)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Search Depth (ply)", fontsize=12)
    plt.ylabel("Mean Nodes Expanded", fontsize=12)
    plt.yscale("log")
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.legend(frameon=True, fontsize=11)
    plt.tight_layout()
    nodes_plot_path = os.path.join(output_dir, "benchmark_depth_vs_nodes.png")
    plt.savefig(nodes_plot_path, dpi=300)
    plt.close()
    print(f"Saved plot: {nodes_plot_path}")

    # 3. Minimax vs Alpha-Beta Node Comparison at Depth 3
    d3_df = df[(df["depth"] == 3) & (df["algorithm"].isin(search_algos))]
    if not d3_df.empty:
        pivot_d3 = d3_df.pivot(index="position", columns="algorithm", values="nodes_expanded")
        plt.figure(figsize=(10, 6))
        ax = pivot_d3.plot(kind="bar", figsize=(10, 6), width=0.75, colormap="viridis")
        plt.title("Nodes Expanded Comparison at Depth 3 (Minimax vs Alpha-Beta)", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Test Position", fontsize=12)
        plt.ylabel("Nodes Expanded", fontsize=12)
        plt.xticks(rotation=15, ha="right", fontsize=10)
        plt.yscale("log")
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        plt.legend(title="Algorithm", frameon=True)
        plt.tight_layout()
        comparison_plot_path = os.path.join(output_dir, "benchmark_minimax_vs_alphabeta.png")
        plt.savefig(comparison_plot_path, dpi=300)
        plt.close()
        print(f"Saved plot: {comparison_plot_path}")

    # 4. Pruning Efficiency (% Reduction in Nodes Expanded relative to Minimax at Depth 3)
    if not d3_df.empty:
        pos_names = []
        reduction_ab = []
        reduction_abo = []

        for pos in df["position"].unique():
            pos_data = d3_df[d3_df["position"] == pos]
            mm_nodes = pos_data[pos_data["algorithm"] == "Minimax"]["nodes_expanded"].values
            ab_nodes = pos_data[pos_data["algorithm"] == "Alpha-Beta"]["nodes_expanded"].values
            abo_nodes = pos_data[pos_data["algorithm"] == "Alpha-Beta (Ordered)"]["nodes_expanded"].values

            if len(mm_nodes) > 0 and len(ab_nodes) > 0 and len(abo_nodes) > 0:
                mm = mm_nodes[0]
                pct_ab = ((mm - ab_nodes[0]) / mm) * 100.0
                pct_abo = ((mm - abo_nodes[0]) / mm) * 100.0
                pos_names.append(pos)
                reduction_ab.append(pct_ab)
                reduction_abo.append(pct_abo)

        x = np.arange(len(pos_names))
        width = 0.35

        plt.figure(figsize=(9, 5))
        plt.bar(x - width/2, reduction_ab, width, label="Alpha-Beta (Unordered)", color="#3b82f6")
        plt.bar(x + width/2, reduction_abo, width, label="Alpha-Beta (Move Ordered)", color="#10b981")

        plt.title("Pruning Efficiency: % Node Reduction vs Minimax (Depth 3)", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Controlled Position", fontsize=12)
        plt.ylabel("Node Reduction (%)", fontsize=12)
        plt.xticks(x, pos_names, fontsize=10)
        plt.ylim(0, 100)
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        plt.legend(frameon=True, fontsize=11)
        plt.tight_layout()
        pruning_plot_path = os.path.join(output_dir, "benchmark_pruning_efficiency.png")
        plt.savefig(pruning_plot_path, dpi=300)
        plt.close()
        print(f"Saved plot: {pruning_plot_path}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = run_benchmarks(depths=[1, 2, 3])
    
    csv_path = os.path.join(OUTPUT_DIR, "benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved CSV benchmark results to: {csv_path}")

    generate_visualizations(df, OUTPUT_DIR)
    print("\nBenchmark analysis completed successfully.")

if __name__ == "__main__":
    main()
