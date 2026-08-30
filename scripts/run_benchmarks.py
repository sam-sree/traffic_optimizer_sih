import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.benchmarking.runner import BenchmarkRunner
from backend.app.benchmarking.report_generator import generate_benchmark_reports

def main():
    print("=" * 80)
    print("QuantumRoute: Executing Head-to-Head Benchmarking Suite")
    print("=" * 80)

    runner = BenchmarkRunner(num_seeds=3) # 3 seeds per stochastic algorithm for quick execution
    results = runner.run_benchmark_suite(sizes=[20, 50, 100])

    print("\n[Benchmarking] Generating final reports and exports...")
    generate_benchmark_reports(results)

    print("\n" + "=" * 80)
    print("Benchmarking Suite Completed Successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
