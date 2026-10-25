from statistics import mean, stdev
from backend.services.adaptive_detector import classify_interval
from tests.compare_detectors import generate_cases, calculate_metrics

results = []

for seed in range(100, 130):
    cases = generate_cases(seed=seed)
    actual, fixed, adaptive = [], [], []

    for interval, jitter, label, category in cases:
        result = classify_interval(
            mean_interval=5.0,
            std_interval=0.2,
            observed_interval=interval,
            observed_jitter=jitter,
            baseline_jitter=1.0
        )

        if not result["ready"]:
            raise RuntimeError("Unexpected invalid observation")

        actual.append(label)
        fixed.append(result["fixed_anomaly"])
        adaptive.append(result["anomaly"])

    fm = calculate_metrics(actual, fixed)
    am = calculate_metrics(actual, adaptive)

    results.append({
        "accuracy": (am["accuracy"] - fm["accuracy"]) * 100,
        "f1": (am["f1"] - fm["f1"]) * 100,
        "fpr": (am["fpr"] - fm["fpr"]) * 100,
        "recall": (am["recall"] - fm["recall"]) * 100,
        "fp_reduced": fm["FP"] - am["FP"],
        "fn_added": am["FN"] - fm["FN"]
    })

print("GOAL B - PRODUCTION CLASSIFIER VALIDATION")
print("=" * 55)

for metric in ("accuracy", "f1", "fpr", "recall"):
    values = [row[metric] for row in results]
    print(
        f"{metric:<12} Mean: {mean(values):+.3f} pp "
        f"SD: {stdev(values):.3f}"
    )

print(f"Average false positives avoided: "
      f"{mean(row['fp_reduced'] for row in results):.2f}")
print(f"Average additional missed attacks: "
      f"{mean(row['fn_added'] for row in results):.2f}")
print(f"Higher accuracy in "
      f"{sum(row['accuracy'] > 0 for row in results)}/30 runs")
print("No database writes performed.")
