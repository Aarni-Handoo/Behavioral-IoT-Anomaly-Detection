
import random
import time

from backend.services.adaptive_detector import classify_interval


def calculate_metrics(actual, predicted):
    tp = sum(a and p for a, p in zip(actual, predicted))
    tn = sum(not a and not p for a, p in zip(actual, predicted))
    fp = sum(not a and p for a, p in zip(actual, predicted))
    fn = sum(a and not p for a, p in zip(actual, predicted))

    total = len(actual)

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": (tp + tn) / total if total else 0,
        "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / (tp + fn) if tp + fn else 0,
        "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0,
        "fpr": fp / (fp + tn) if fp + tn else 0,
    }


def generate_cases(seed=42):
    rng = random.Random(seed)
    cases = []

    # 1. Normal traffic under ordinary jitter
    for _ in range(250):
        cases.append((
            max(0, rng.gauss(5.0, 0.2)),
            rng.uniform(0.8, 1.2),
            False,
            "normal"
        ))

    # 2. Legitimate traffic under high network jitter
    for _ in range(250):
        cases.append((
            max(0, rng.gauss(5.0, 0.9)),
            rng.uniform(1.5, 2.5),
            False,
            "noisy_normal"
        ))

    # 3. Obvious attacks under ordinary jitter
    for _ in range(250):
        cases.append((
            rng.choice([3.5, 6.5]) + rng.gauss(0, 0.15),
            rng.uniform(0.8, 1.2),
            True,
            "attack"
        ))

    # 4. Attacks during high network jitter
    for _ in range(250):
        cases.append((
            rng.choice([4.15, 5.85]) + rng.gauss(0, 0.08),
            rng.uniform(1.5, 2.5),
            True,
            "noisy_attack"
        ))

    rng.shuffle(cases)
    return cases


def run_experiment():
    cases = generate_cases()

    actual = []
    fixed_predictions = []
    adaptive_predictions = []

    for interval, jitter, label, category in cases:
        result = classify_interval(
            mean_interval=5.0,
            std_interval=0.2,
            observed_interval=interval,
            observed_jitter=jitter,
            baseline_jitter=1.0
        )

        if not result["ready"]:
            raise RuntimeError("Unexpected invalid test case")

        actual.append(label)
        fixed_predictions.append(result["fixed_anomaly"])
        adaptive_predictions.append(result["anomaly"])

    print("\nGOAL B RESEARCH COMPARISON")
    print("=" * 65)
    print(f"Total labelled synthetic cases: {len(cases)}")
    print("Seed: 42")
    print("Baseline mean: 5.0 seconds")
    print("Baseline std: 0.2 seconds")
    print("Baseline jitter: 1.0 ms")

    for name, predictions in [
        ("Fixed Z-score", fixed_predictions),
        ("Adaptive Z-score", adaptive_predictions)
    ]:
        m = calculate_metrics(actual, predictions)

        print(f"\n{name}")
        print("-" * 40)
        print(
            f"TP={m['TP']} TN={m['TN']} "
            f"FP={m['FP']} FN={m['FN']}"
        )
        print(f"Accuracy:  {m['accuracy'] * 100:.2f}%")
        print(f"Precision: {m['precision'] * 100:.2f}%")
        print(f"Recall:    {m['recall'] * 100:.2f}%")
        print(f"F1-score:  {m['f1'] * 100:.2f}%")
        print(f"FPR:       {m['fpr'] * 100:.2f}%")

    # Repeated timing reduces the noise from individual calls.
    for name, field in [
        ("Fixed decision", "fixed_anomaly"),
        ("Adaptive decision", "anomaly")
    ]:
        start = time.perf_counter()

        for _ in range(100):
            for interval, jitter, label, category in cases:
                result = classify_interval(
                    5.0, 0.2, interval,
                    observed_jitter=jitter,
                    baseline_jitter=1.0
                )
                _ = result[field]

        elapsed = time.perf_counter() - start
        average_us = elapsed / (100 * len(cases)) * 1_000_000
        print(f"{name} average calculation: {average_us:.3f} us")

    print("\nNo MySQL database writes were performed.")


if __name__ == "__main__":
    run_experiment()
