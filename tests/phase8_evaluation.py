
import time


def detect_interval_anomaly(mean_interval, std_interval, observed_interval):
    if mean_interval is None:
        mean_interval = 0.0

    if std_interval is None or std_interval <= 0:
        std_interval = 0.01

    deviation = abs(observed_interval - mean_interval)
    score = deviation / std_interval

    score = round(score, 10)
    return score > 3, round(score, 2)


def evaluate_cases():
    cases = [
        ("Normal traffic", 2.0, 0.2, 2.1, False),
        ("Slight variation", 2.0, 0.2, 2.4, False),
        ("Abnormal interval", 2.0, 0.2, 3.0, True),
        ("Extreme interval", 2.0, 0.2, 4.0, True),
        ("Zero standard deviation", 2.0, 0.0, 2.0, False),
        ("Missing standard deviation", 2.0, None, 2.0, False),
        ("Missing mean", None, 0.2, 0.1, False),
        ("Exact threshold", 2.0, 0.2, 2.6, False),
        ("Just above threshold", 2.0, 0.2, 2.61, True),
        ("Lower abnormal interval", 2.0, 0.2, 1.0, True),
    ]

    tp = tn = fp = fn = 0
    total_time = 0

    print("\nPHASE 8: EDGE-CASE EVALUATION")
    print("-" * 76)

    for name, mean, std, observed, expected in cases:
        start = time.perf_counter()
        detected, score = detect_interval_anomaly(mean, std, observed)
        elapsed = time.perf_counter() - start
        total_time += elapsed

        if detected and expected:
            tp += 1
            result = "TP"
        elif not detected and not expected:
            tn += 1
            result = "TN"
        elif detected:
            fp += 1
            result = "FP"
        else:
            fn += 1
            result = "FN"

        status = "PASS" if detected == expected else "FAIL"

        print(
            f"{name:<28} Score={score:<8} "
            f"Detected={str(detected):<6} "
            f"{result:<3} {status}"
        )

    total = len(cases)
    accuracy = (tp + tn) / total * 100
    precision = tp / (tp + fp) * 100 if tp + fp else 0
    recall = tp / (tp + fn) * 100 if tp + fn else 0

    print("-" * 76)
    print(f"Test cases: {total}")
    print(f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"Accuracy:  {accuracy:.2f}%")
    print(f"Precision: {precision:.2f}%")
    print(f"Recall:    {recall:.2f}%")
    print(f"Total evaluation time: {total_time * 1000:.3f} ms")
    print(f"Average time per case: {total_time / total * 1000:.3f} ms")
    print("\nNo database records were modified.")


if __name__ == "__main__":
    evaluate_cases()
