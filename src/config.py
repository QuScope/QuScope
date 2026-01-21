"""Configuration management for quantum microscopy system."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class QuantumConfig:
    """Quantum algorithm configuration."""

    backend_name: str = "qasm_simulator"
    shots: int = 1024
    max_qubits: int = 20
    optimization_level: int = 2
    seed: Optional[int] = None
    noise_model: Optional[str] = None


@dataclass
class ProcessingConfig:
    """Classical processing configuration."""

    batch_size: int = 100
    max_workers: int = 4
    cache_enabled: bool = True
    cache_size: int = 1000


@dataclass
class VisualizationConfig:
    """Visualization configuration."""

    figure_size: tuple = (12, 8)
    dpi: int = 300
    color_scheme: str = "viridis"
    animation_fps: int = 30
    save_format: str = "png"


@dataclass
class Config:
    """Main configuration class."""

    quantum: QuantumConfig = field(default_factory=QuantumConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, "r") as f:
            config_data = json.load(f)

        return cls(
            quantum=QuantumConfig(**config_data.get("quantum", {})),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            visualization=VisualizationConfig(**config_data.get("visualization", {})),
        )

    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_data = {
            "quantum": self.quantum.__dict__,
            "processing": self.processing.__dict__,
            "visualization": self.visualization.__dict__,
        }

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
