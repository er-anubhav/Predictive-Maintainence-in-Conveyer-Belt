import json
from typing import Dict, Any, List, Tuple
import numpy as np


class GroupedDataSplitter:
    """
    Prevents data leakage across train/val/test splits.
    Windows from the same continuous run, machine, or physical bearing
    are NEVER split across train and test partitions.
    """

    @staticmethod
    def split_by_group(
        records: List[Dict[str, Any]],
        group_key: str = "machine_id",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Splits dataset by distinct group keys (e.g. bearing ID or machine ID).
        Guarantees that test records come from unseen physical entities or runs.
        """
        np.random.seed(random_seed)
        
        # Group samples by the chosen entity
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            g = str(r.get(group_key, "unknown"))
            groups.setdefault(g, []).append(r)

        unique_groups = sorted(list(groups.keys()))
        np.random.shuffle(unique_groups)

        n_groups = len(unique_groups)
        n_train = max(1, int(round(n_groups * train_ratio)))
        n_val = int(round(n_groups * val_ratio))
        
        train_groups = unique_groups[:n_train]
        val_groups = unique_groups[n_train:n_train + n_val]
        test_groups = unique_groups[n_train + n_val:]
        if not test_groups and len(unique_groups) > 1:
            # ensure test set has at least 1 group if multiple exist
            test_groups = [val_groups.pop()] if val_groups else [train_groups.pop()]

        train_data = [item for g in train_groups for item in groups[g]]
        val_data = [item for g in val_groups for item in groups[g]]
        test_data = [item for g in test_groups for item in groups[g]]

        split_metadata = {
            "group_key": group_key,
            "random_seed": random_seed,
            "train_groups": train_groups,
            "val_groups": val_groups,
            "test_groups": test_groups,
            "train_samples": len(train_data),
            "val_samples": len(val_data),
            "test_samples": len(test_data),
            "leakage_verified": len(set(train_groups).intersection(set(test_groups))) == 0,
        }

        return train_data, val_data, test_data, split_metadata
