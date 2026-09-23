import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
import numpy as np


class ExperimentTracker:
    """Tracks training runs, metrics, and dataset provenance across experiments."""

    def __init__(self, log_dir: str = "ml/experiments"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log_experiment(
        self,
        experiment_id: str,
        dataset: str,
        dataset_version: str,
        feature_version: str,
        processing_version: str,
        model_type: str,
        hyperparameters: Dict[str, Any],
        random_seed: int,
        train_samples: int,
        validation_samples: int,
        test_samples: int,
        metrics: Dict[str, Any],
        notes: str = "",
    ) -> str:
        record = {
            "experiment_id": experiment_id,
            "dataset": dataset,
            "dataset_version": dataset_version,
            "feature_version": feature_version,
            "processing_version": processing_version,
            "model_type": model_type,
            "hyperparameters": hyperparameters,
            "random_seed": random_seed,
            "train_samples": train_samples,
            "validation_samples": validation_samples,
            "test_samples": test_samples,
            "metrics": metrics,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        filepath = os.path.join(self.log_dir, f"{experiment_id}.json")
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)

        return filepath


class ModelEvaluator:
    """
    Evaluates anomaly detection performance with separated validation groups:
    - SYNTHETIC VALIDATION
    - PUBLIC DATASET VALIDATION
    - REAL CONVEYOR VALIDATION
    Strictly avoids combining different domains into a single misleading accuracy score.
    """

    @staticmethod
    def evaluate(
        y_true_binary: List[int], # 0 = Normal, 1 = Anomalous
        y_pred_binary: List[int],
        scores: List[float],
        evaluation_domain: str = "PUBLIC DATASET VALIDATION",
    ) -> Dict[str, Any]:
        y_true = np.array(y_true_binary)
        y_pred = np.array(y_pred_binary)

        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))

        precision = round(float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0, 4)
        recall = round(float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0, 4)
        f1 = round(float(2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0, 4)
        fpr = round(float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0, 4)

        return {
            "evaluation_domain": evaluation_domain,
            "samples_evaluated": len(y_true),
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "false_positive_rate": fpr,
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
            },
            "score_distribution": {
                "mean": round(float(np.mean(scores)), 4) if len(scores) else 0.0,
                "std": round(float(np.std(scores)), 4) if len(scores) else 0.0,
                "min": round(float(np.min(scores)), 4) if len(scores) else 0.0,
                "max": round(float(np.max(scores)), 4) if len(scores) else 0.0,
            }
        }
