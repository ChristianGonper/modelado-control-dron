"""Phase 2 dataset contract, extraction and feature builders."""

from .contract import (
    BASE_FEATURE_NAMES,
    DATASET_TARGET_NAMES,
    ERROR_FEATURE_NAMES,
    FEATURE_MODES,
    PHASE2_DATASET_CONTRACT,
    DatasetContract,
    DatasetEpisode,
    DatasetSample,
    DatasetSplitContext,
    DatasetTraceability,
)
from .extract import (
    DatasetExtractionError,
    extract_dataset_episode,
    extract_dataset_episodes,
    load_dataset_episode,
    load_dataset_episodes,
)
from .features import (
    build_feature_matrix,
    build_feature_vector,
    build_target_matrix,
    build_target_vector,
    feature_dimension_for_mode,
    feature_names_for_mode,
    target_dimension,
    target_names,
)

__all__ = [
    "BASE_FEATURE_NAMES",
    "DATASET_TARGET_NAMES",
    "DatasetContract",
    "DatasetEpisode",
    "DatasetExtractionError",
    "DatasetSample",
    "DatasetSplitContext",
    "DatasetTraceability",
    "ERROR_FEATURE_NAMES",
    "FEATURE_MODES",
    "PHASE2_DATASET_CONTRACT",
    "build_feature_matrix",
    "build_feature_vector",
    "build_target_matrix",
    "build_target_vector",
    "extract_dataset_episode",
    "extract_dataset_episodes",
    "feature_dimension_for_mode",
    "feature_names_for_mode",
    "load_dataset_episode",
    "load_dataset_episodes",
    "target_dimension",
    "target_names",
]
