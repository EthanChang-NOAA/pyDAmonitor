"""
A script that generates a time series plot showing the hourly observation count for a single satellite instrument channel. It searches the com directory (after specifying the model and version) for observer files and extracts the observation count after one QC pass (`n_loop1`) for a requested channel.

NOTE: Channel numbers are instrument-specific. Comparing the same channel number across different instruments is usually not meaningful.

TODO: This script should work when run by itself or called by another script as a task (e.g. integrating plots)
TODO: Start and end time options for users to specify if they have an experiment that spans a time period larger than what they want the time series to show

Author: Ethan Chang
"""

from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import parseargs_script
import importlib

importlib.reload(parseargs_script)

if __name__ == "__main__":
    args = parseargs_script.get_args_single_channel_timeseries()
    com_directory = Path(args.com_directory)
    observer = args.observer
    requested_channel = args.channel

    file_map = {}
    all_times = set()

    print(f"Discovering files in {com_directory}...")

    # Parse date information in com directory. This can handle multiple days of data, but visualization may be challenging (see labeling comment towards the end of the script)
    for run_dir in sorted(com_directory.glob("rrfs.*")):
        date_str = run_dir.name.split(".")[1]

        # Read counts from observer file
        for hour_dir in sorted(run_dir.glob("[0-2][0-9]")):
            dt = datetime.strptime(date_str + hour_dir.name, "%Y%m%d%H")
            all_times.add(dt)

            obs_file = hour_dir / "pyDAmonitor/det" / f"{observer}.txt"

            if obs_file.exists():
                file_map[dt] = obs_file

    timeline = sorted(all_times)

    # EXTRACT INFORMATION
    all_obs_counts = []

    for dt in timeline:
        obs_file = file_map.get(dt)

        if obs_file is None:
            all_obs_counts.append(np.nan)  # Avoid calling open(None)
            continue

        obs_count = np.nan  # Default to NaN if obs_count never gets set below (e.g. if requested channel doesn't exist or is invalid)

        with open(obs_file) as file:
            for line in file:
                parts = line.split()

                if len(parts) < 2:
                    continue

                channel_str = parts[0]
                n_loop1 = parts[1]

                # Skip strings in the channel column if they don't have numbers in them (i.e. headers)
                if not channel_str.isdigit():
                    continue

                # Cast channel numbers from strings to ints
                converted_ch = int(channel_str)
                if converted_ch != requested_channel:
                    continue

                try:
                    # Cast obs counts from strings to ints
                    obs_count = int(n_loop1)
                except ValueError:
                    print(
                        f"WARNING: Could not convert observation count ({n_loop1}) for {channel_str} to int!"
                    )
                    continue

                break  # If we already reached the requested_channel in the file and it's valid, just ignore the rest of the file

        all_obs_counts.append(obs_count)

    all_obs_counts = np.array(
        all_obs_counts, dtype=float
    )  # Float arrays can support NaN values even if each obs_count is an integer

    # PLOT
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(timeline, all_obs_counts, marker="o", linewidth=1.5)

    ax.set_title(
        f"Number of {observer} Observations by Hour | Channel {requested_channel}"
    )
    ax.set_xlabel("Day and Time (UTC)")
    ax.set_ylabel("Number of Observations")

    # NOTE: If the time period spans more than a day, the x-axis labels may become quite dense
    # TODO: Something that would resolve this problem or give the user more options on controlling how the labels will display
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d\n%H"))

    # ax.margins(x=0)

    ax.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()

    figures_dir = Path("figures")
    if not figures_dir.exists():
        figures_dir.mkdir()
        print(f'Figure directory "{figures_dir}" does not exist! Creating one...')
    fig.savefig(f"{figures_dir}/{observer}_{requested_channel}.png", dpi=150)
    plt.show()
