"""
Functions that should work for all my scripts.

Author: Ethan Chang
"""

from datetime import datetime, timedelta
from pathlib import Path
from netCDF4 import Dataset
import numpy as np


def read_obs_count_file(filepath: Path) -> dict:
    """
    Read an observation count summary file and return the observation counts for each observer.

    The expected file format is as follows:
        observer  n_ioda  nobs  nobs_r  n_loop1  n_loop2

    Example:
        cris-fsr_n21  12345  12000  10000  9000  9000

    Returns:
        Dictionary keyed by observer name.

        Example:
        {
            "cris-fsr_n21": {
                "n_ioda": 12345.0,
                "nobs": 12000.0,
                "nobs_r": 10000.0,
                "n_loop1": 9000.0,
                "n_loop2": 9000.0,
            }
        }
    """
    counts = {}

    with filepath.open() as f:
        for line in f:
            parts = line.split()

            if len(parts) < 6:
                continue

            observer = parts[0]

            try:
                counts[observer] = {
                    "n_ioda": float(parts[1]),
                    "nobs": float(parts[2]),
                    "nobs_r": float(parts[3]),
                    "n_loop1": float(parts[4]),
                    "n_loop2": float(parts[5]),
                }

            except ValueError:
                continue

    return counts


def find_first_jdiag_file(base_path: Path, observer: str, model_acronym: Path, task_subdirectory: Path, wgf: Path) -> Path:
    """
    Find the earliest jdiag file for an observer. Used for discovering the available channels for an observer, so the specific cycle does not matter.

    Assumes the following structure:
    base_path/
        model_acronym.YYYYMMDD/
            HH/
                task_subdirectory/wgf/
                    jdiag_<observer>.nc
    """

    matches = sorted(
        base_path.glob(f"{model_acronym}.*/[0-2][0-9]/{task_subdirectory}/{wgf}/jdiag_{observer}.nc")
    )

    if not matches:
        raise FileNotFoundError(f"No jdiag file found for {observer} under {base_path}")

    return matches[0]


def get_available_channels(jdiag_file: Path) -> np.ndarray:
    """
    Reads in a jdiag NetCDF file and returns a NumPy array containing the channel numbers.
    """

    with Dataset(jdiag_file) as ncd:
        return np.asarray(ncd.variables["Channel"][:])


def validate_requested_channels(
    requested_channels: list[int],
    available_channels: np.ndarray,
) -> None:
    """
    Check that the requested channels exist (compares them with what is received from get_available_channels()).
    """

    missing = [ch for ch in requested_channels if ch not in available_channels]

    if missing:
        raise ValueError(
            f"The following requested channel(s) were not found: {missing}. "
            f"Available channels: {available_channels}"
        )


def get_channel_index(jdiag_file: Path, target_channel: int) -> int:
    """
    Return the array index corresponding to the requested channel.

    Used for OmB map.
    """
    available_channels = get_available_channels(jdiag_file)

    validate_requested_channels(
        [target_channel],
        available_channels,
    )

    return int(np.where(available_channels == target_channel)[0][0])


def get_cycle_directory(
    base: Path,
    model_acronym: str,
    dt: datetime,
    task_subdirectory: Path,
    wgf: Path,
) -> Path:
    """
    Construct the path to the folder containing files for the particular rrfs-workflow task.
    """

    return (
        base
        / f"{model_acronym}.{dt:%Y%m%d}"
        / f"{dt:%H}"
        / task_subdirectory
        / wgf
    )


def find_cycle_file(cycle_dir: Path, filename: str) -> Path | None:
    """
    Search for a file given a path.

    Returns None if the file does not exist in either cycle_dir or cycle_dir/web.

    Needs to be called after get_cycle_directory()
    """
    path = cycle_dir / filename
    if path.exists():
        return path

    path = cycle_dir / "web" / filename
    if path.exists():
        return path

    return None


def build_timeline(
    end_date: str,
    lookback_hours: int,
) -> tuple[datetime, datetime, list[datetime]]:
    """
    Builds an hourly timeline inclusive of the last hour.

    Example:
    end = 12Z, lookback = 6 -> 06, 07, 08, 09, 10, 11, 12
    """

    if lookback_hours < 0:
        raise ValueError("lookback_hours must be non-negative")

    date_end = datetime.strptime(end_date, "%Y%m%d%H")
    date_begin = date_end - timedelta(hours=lookback_hours)

    timeline = [
        date_begin + timedelta(hours=i)
        for i in range(lookback_hours + 1)
    ]

    return date_begin, date_end, timeline
