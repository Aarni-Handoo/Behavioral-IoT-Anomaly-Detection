
import csv
import random
from pathlib import Path

from backend.services.adaptive_detector import classify_interval
from tests.compare_detectors import generate_cases, calculate_metrics


def adaptive_decision(score, jitter, baseline_jitter, strength, cap):
    ratio = jitter / baseline_jitter
    threshold = 3.0 + min(
        cap,
        strength * max(0.0, ratio - 1.0)
    )
    return score > round(threshold, 10)


def evaluate_settings(cases, strength, cap):
    labels = []
    predictions = []
    categories = {}

    for interval, jitter, is_attack, category in cases:
        result = classify_interval(
            mean_interval=5.0,
            std_interval=0.2,
            observed_interval=interval,
            observed_jitter=jitter,
            baseline_jitter=1.0
        )

        score = result["score"]
        prediction = adaptive_decision(
            score, jitter, 1.0, strength, cap
        )

        labels.append(is_attack)
        predictions.append(prediction)

        if category not in categories:
            categories[category] = {
                "labels": [],
                "predictions": []
            }

        categories[category]["labels"].append(is_attack)
        categories[category]["predictions"].append(prediction)

    overall = calculate_metrics(labels, predictions)

    category_results = {
        name: calculate_metrics(
            values["labels"],
            values["predictions"]
        )
        for name, values in categories.items()
    }

    return overall, category_results


def main():
    # Separate tuning and evaluation data
    training_cases = generate_cases(seed=42)
    holdout_cases = generate_cases(seed=2026)

    settings = [
        (0.0, 0.0),  # Original fixed Z-score
        (0.25, 0.25),
        (0.5, 0.5),
        (0.75, 0.75),
        (1.0, 1.0),
        (1.5, 1.5),
        (2.0, 2.0),  # Current Goal B
    ]

    rows = []

    print("\nGOAL B — THRESHOLD SENSITIVITY STUDY")
    print("=" * 85)

    for strength, cap in settings:
        metrics, categories = evaluate_settings(
            training_cases, strength, cap
        )

        rows.append({
            "strength": strength,
            "cap": cap,
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "fpr": metrics["fpr"],
            "fp": metrics["FP"],
            "fn": metrics["FN"],
        })

        print(
            f"Strength={strength:<4} Cap={cap:<4} "
            f"Accuracy={metrics['accuracy'] * 100:6.2f}% "
            f"Recall={metrics['recall'] * 100:6.2f}% "
            f"FPR={metrics['fpr'] * 100:6.2f}% "
            f"FP={metrics['FP']:3} "
            f"FN={metrics['FN']:3}"
        )

        if strength in (0.0, 1.0, 2.0):
            print(
                "   By category:",
                " | ".join(
                    f"{name}: FP={m['FP']}, FN={m['FN']}"
                    for name, m in categories.items()
                )
            )

    # Illustrative tuning criterion:
    # Maximize F1 while requiring at least 90% recall.
    eligible = [r for r in rows if r["recall"] >= 0.90]

    if not eligible:
        print("\nNo setting satisfied the recall requirement.")
        return

    best = max(
        eligible,
        key=lambda r: (r["f1"], -r["fpr"])
    )

    print("\nBEST SETTING ON TUNING DATA")
    print(best)

    holdout, holdout_categories = evaluate_settings(
        holdout_cases,
        best["strength"],
        best["cap"]
    )

    print("\nHELD-OUT SYNTHETIC EVALUATION")
    print(f"Accuracy: {holdout['accuracy'] * 100:.2f}%")
    print(f"Precision: {holdout['precision'] * 100:.2f}%")
    print(f"Recall: {holdout['recall'] * 100:.2f}%")
    print(f"F1-score: {holdout['f1'] * 100:.2f}%")
    print(f"FPR: {holdout['fpr'] * 100:.2f}%")
    print(f"FP={holdout['FP']} FN={holdout['FN']}")

    print("\nHeld-out category breakdown:")
    for name, metrics in sorted(holdout_categories.items()):
        print(
            f"  {name:<15} "
            f"TP={metrics['TP']:3} "
            f"TN={metrics['TN']:3} "
            f"FP={metrics['FP']:3} "
            f"FN={metrics['FN']:3}"
        )

    output = Path("reports")
    output.mkdir(exist_ok=True)

    with (output / "goal_b_threshold_sensitivity.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSaved: reports/goal_b_threshold_sensitivity.csv")
    print("No database writes performed.")


if __name__ == "__main__":
    main()
