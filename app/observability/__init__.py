"""Observability & experiment tracking package for MindLayer.

Provides:
  - `tracker.RunTracker`        MLflow-style run logger (SQLite-backed)
  - `experiments.Experiment`    High-level experiment definition + result aggregation
  - `artifacts.ArtifactStore`   Save/load prompt versions, datasets, configs
  - `cost.CostTracker`          Per-call LLM cost attribution
"""
