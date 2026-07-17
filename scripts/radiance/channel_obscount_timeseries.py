"""
A script that generates a time series plot showing the hourly observation count for a single satellite instrument channel. It searches the com directory (after specifying the model and version) for observer files and extracts the observation count after one QC pass (`n_loop1`) for a requested channel.

NOTE: Channel numbers are instrument-specific. Comparing the same channel number across different instruments is usually not meaningful.
TODO: This script should work when called by another script as a task (e.g. integrating plots)

Author: Ethan Chang
"""
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from shared import argparser, shared_functions
import importlib
import logging


def sum_requested_channels_counts(channel_data, requested_channels):
    """
    Calculates the total observation count at each hour based on summing up the counts of ONLY the requested channels. (So, you cannot use obs_count.txt)

    Channels that have NaN or 0 do not contribute to this plot.
    """
    total = 0

    for ch in requested_channels:
        if ch not in channel_data:
            continue

        total += channel_data[ch]

    return total


def read_channel_counts(filepath):
    """
    Reads the observation counts from the observer file. 

    TODO? Optimize to only read requested channels because we already do validation from the jdiag at the get-go. Rename then to read_requested_channel_counts()
    """
    kept = {}

    with open(filepath, "r") as f:
        for line in f:
            parts = line.split()

            if len(parts) < 2:
                continue

            channel_str = parts[0]
            count_str = parts[1]

            # Skip header or non-channel lines
            if not channel_str.isdigit():
                continue

            try:
                channel = int(channel_str)
                count = float(count_str)
            except ValueError:
                logging.warning(
                    f"Could not convert count ({count_str}) "
                    f"for channel {channel_str}"
                )
                continue

            kept[channel] = count

    return kept


def list_missing_files(missing_files, observer):
    """
    Helper function that lists any observer.txt files that are missing (i.e. do not exist)
    """

    lines = [
        f"Missing {observer}.txt files at {len(missing_files)} hours:"
    ]

    times_by_date = defaultdict(list)

    for t in missing_files:
        times_by_date[t.date()].append(t)

    for date, times in sorted(times_by_date.items()):
        hour_str = ", ".join(f"{t:%HZ}" for t in sorted(times))
        lines.append(f"  {date}: {hour_str}")

    logging.warning("\n".join(lines))


def list_absent_channels(absent_channels):
    """
    Helper function that lists any channels that are absent from existing observer.txt files
    """
    for ch, times in absent_channels.items():
        times_by_date = defaultdict(list)

        for t in times:
            times_by_date[t.date()].append(t)

        lines = [
            f"Requested channel {ch} absent from existing files at {len(times)} hours:"
        ]

        for date, hours in sorted(times_by_date.items()):
            hour_str = ", ".join(f"{t:%HZ}" for t in sorted(hours))
            lines.append(f"  {date}: {hour_str}")

        logging.warning("\n".join(lines))


def plot_series(requested_channels, observer, timeline, requested_channel_totals_allhours, channel_counts):
    """
    Plot the time series, returning the plt for further use as well
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    if len(requested_channels) > 1:
        ax.plot(
            timeline,
            requested_channel_totals_allhours,
            marker="o",
            linewidth=1.5,
            label="Sum of Requested Channels Observations",
        )

    for ch in requested_channels:
        ax.plot(
            timeline,
            channel_counts[ch],
            marker="o",
            linewidth=1.5,
            label=f"Channel {ch}",
        )

    ax.legend()

    title_range = (
        f"{timeline[0].strftime('%Y-%m-%d %H UTC')} – "
        f"{timeline[-1].strftime('%Y-%m-%d %H UTC')}"
    )

    ax.set_title(
        f"Number of {observer} Observations by Hour | Channels: {requested_channels}\n{title_range}"
    )
    ax.set_xlabel("Day and Time (UTC)")
    ax.set_ylabel("Number of Observations")

    # NOTE: If the time period spans more than a day, the x-axis labels may become quite dense
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d\n%H"))

    ax.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()

    figures_dir = Path("figures")
    if not figures_dir.exists():
        figures_dir.mkdir()
        print(f'Figure directory "{figures_dir}" does not exist! Creating one...')
    fig.savefig(f"{figures_dir}/{observer}_{requested_channels}.png", dpi=150)

    return plt


if __name__ == "__main__":
    importlib.reload(argparser)
    importlib.reload(shared_functions)
    args = argparser.get_args_single_observer_timeseries()
    com_path = Path(args.com_directory)
    exp_path = Path(args.exp_subdirectory)
    model_acronym = Path(exp_path.parts[0])  # e.g. "rrfs"
    pyDAmonitor_path = Path(args.task_subdirectory)
    wgf = Path(args.wgf)
    observer = args.observer
    requested_channels = args.channels
    CDATE = args.end_date
    LOOKBACK_HOURS = args.lookback_hours

    base_path = com_path / exp_path
    print(f"Reading files in {base_path}...")

    # Inspect the first jdiag file to find out which channels exist
    jdiag_file = shared_functions.find_first_jdiag_file(
        base_path,
        observer,
        model_acronym,
        pyDAmonitor_path,
        wgf
    )
    available_channels = shared_functions.get_available_channels(jdiag_file)

    # Validate that the channels requested even exist before doing anything else by comparing the requested channels to the information in the file we just read
    shared_functions.validate_requested_channels(
        requested_channels,
        available_channels,
    )

    # Build timeline
    _, _, timeline = shared_functions.build_timeline(
        CDATE,
        LOOKBACK_HOURS,
    )

    # EXTRACT INFORMATION
    requested_channel_totals = []
    channel_counts: dict[int, list[float]] = {
        ch: [] for ch in requested_channels
    }
    missing_files = []
    absent_channels = defaultdict(list)

    for dt in timeline:
        cycle_dir = shared_functions.get_cycle_directory(
            base_path,
            model_acronym,
            dt,
            pyDAmonitor_path,
            wgf,
        )

        observer_file = shared_functions.find_cycle_file(
            cycle_dir,
            f"{observer}.txt",
        )

        if observer_file is None:
            missing_files.append(dt)

            requested_channel_totals.append(np.nan)

            for ch in requested_channels:
                channel_counts[ch].append(np.nan)

            continue

        # Extract channel(s) info
        channel_data = read_channel_counts(observer_file)

        # Append to array
        for ch in requested_channels:
            if ch not in channel_data:
                absent_channels[ch].append(dt)
                channel_counts[ch].append(np.nan)
                continue
            channel_counts[ch].append(channel_data[ch])

        # Sum up numbers
        total_count = sum_requested_channels_counts(
            channel_data,
            requested_channels,
        )
        requested_channel_totals.append(total_count)

    requested_channel_totals_allhours = np.array(
        requested_channel_totals, dtype=float
    )  # Float arrays can support NaN values even if each obs_count is an integer

    if missing_files:
        list_missing_files(missing_files, observer=observer)
    if absent_channels:
        list_absent_channels(absent_channels)

    plot = plot_series(requested_channels, observer, timeline, requested_channel_totals_allhours, channel_counts)
    plot.show()
