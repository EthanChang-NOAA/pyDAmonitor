import argparse


def get_args_multichannel_obscounts():
    """
    Use only with the script that plots the observation counts for all channels in a given hour
    """
    parser = argparse.ArgumentParser(
        description="Plot observation counts by channel for a given hour"
    )

    parser.add_argument(
        "--com_directory",
        type=str,
        required=True,
        help="Path to com/rrfs/[version] directory",
    )

    parser.add_argument(
        "--observers",
        nargs="+",
        default=["cris-fsr_n20", "cris-fsr_n21"],
        help="List of observers to plot",
    )

    parser.add_argument(
        "--date",
        type=str,
        required=False,
        default="20240506",
        help="Single run date (YYYYMMDD)",
    )

    parser.add_argument(
        "--hour",
        type=str,
        required=False,
        default="11",
        help="Format must be in 24 hour time and in UTC",
    )
    return parser.parse_args()


def get_args_single_channel_timeseries():
    """
    Use only with channel_obscount_timeseries.py
    """
    parser = argparse.ArgumentParser(
        description="Plot observation counts by hour for a given channel"
    )

    parser.add_argument(
        "--com_directory",
        type=str,
        required=True,
        help="Path to com/rrfs/[version] directory",
    )

    parser.add_argument(
        "--observer",
        type=str,
        required=True,
        help="Which observer?",  # Example: "cris-fsr_n20"
    )

    parser.add_argument("--channel", type=int, required=True, help="Channel number")
    return parser.parse_args()
