# Goal B development handoff (source-compatible extension)

## Preserved
All existing `backend`, `frontend`, `tests`, simulator and database model source paths and the prior Phase 8 evaluator. The existing production anomaly detector and security detector are **unchanged**. No database migrations or new tables. `.env`, `.git` and local `venv` are intentionally absent from this distributable ZIP.

## New adaptive research prototype
- `backend/services/adaptive_detector.py`: a separate pure decision function for a jitter-aware Z-score threshold.
- `GET /adaptive-lab`: read-only comparison UI, accessible from the dashboard navigation.
- `GET /api/adaptive-evaluate/<device_id>?interval=2.8&jitter=1.5`: read-only comparison JSON. Returns `fixed_anomaly`, `anomaly`, `score` and thresholds. Does **not** decrease trust or store detections.
- `tests/test_goal_b.py`: unit and isolated SQLite integration tests.
- `tests/compare_detectors.py`: reproducible **illustrative** synthetic labelled scenarios and CSV output.
- `frontend/templates/adaptive_lab.html` and improvements to the existing dashboard template/CSS.

## Proposed rule (not a claim of novel invention)
`z = abs(interval - mean_interval) / max(std_interval, .01)`.
`T = 3 + min(2, 2 * max(0, observed_jitter/reference_jitter - 1))` when reference jitter is positive and both values valid; otherwise T=3.
Anomaly if `round(z,10) > round(T,10)`.

The reference jitter is approximated using the median from up to the **oldest 100 packet jitter values** recorded for the device. This is a convenient retrospective estimate, **not a rigorously isolated clean training set**, and can be contaminated. Do not present these results as proof of real-world effectiveness; evaluate on held-out labelled data and consider collecting an explicit clean baseline.

Increasing thresholds can **reduce false positives but increase false negatives**. This method is a heuristic extension; novelty and effectiveness remain unproven.

## Run on teammate laptop
1. Copy changes into a **new Git feature branch** after backing up local modifications. Do not overwrite `.env` or the existing local MySQL database.
2. Activate local venv and install `requirements.txt`.
3. `python -m unittest discover -s tests -p 'test_goal_b.py' -v`
4. `python tests/phase8_evaluation.py`
5. `python tests/compare_detectors.py`
6. Start Flask with existing local `.env`: `python app.py` and view `/` and `/adaptive-lab`.
7. Check `git diff --check`, `git status`; stage only intended source files. Do NOT commit `.env`, dumps or secrets.

## Scope of validation
Automated tests cover classification edge cases, read-only API, and template rendering using SQLite. You still need to run live integration and browser QA on your own MySQL installation. The synthetic comparison uses eight **hand-selected** scenarios, so percentages are demonstration examples only. A publishable experiment requires larger labelled data, independent attack scenarios, repeated trials, clear train/test split, and suitable competing baselines.

## Phase map
- Phase 8: original ten-case evaluator preserved; new synthetic fixed-versus-adaptive comparison and tests added. Real-world research validation pending.
- Phase 9: isolated endpoint/database integration tests added. Full local MySQL, actual simulator timing, manual route checks and regression testing still pending.
- Phase 10: improved responsive dashboard and dedicated adaptive analysis page. Browser visual acceptance testing still pending.
- Phase 11: documentation.
- Phase 12: final demonstration/submission readiness (not just documentation).

### Build environment limitation
Python syntax compiled and pure function spot-checked. Flask / SQLAlchemy were not installed in the artifact environment, so database/API integration tests were not executable here. Run them with your existing virtual environment before merging.

### Build environment limitation
Python syntax compiled and pure function spot-checked. Flask / SQLAlchemy were not installed in the artifact environment, so database/API integration tests were not executable here. Run them with your existing virtual environment before merging.
