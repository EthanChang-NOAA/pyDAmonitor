"""
Contains various arguments for different purposes.

Author: Ethan Chang
"""

import argparse


def add_common_args(parser):
    """
    Arguments shared by most radiance DA scripts.
    """

    parser.add_argument(
        "--com-directory",
        type=str,
        required=True,
        help="Path to com directory.",
    )

    parser.add_argument(
        "--exp-subdirectory",
        type=str,
        required=True,
        help="Path to exp subdirectory under com. Example: rrfs/v2.1.4/",
    )

    parser.add_argument(
        "--task-subdirectory",
        type=str,
        required=True,
        help="Path to the task subdirectory under experiment subdirectory. Example: 'jedivar/' or 'pyDAmonitor/",
    )

    parser.add_argument(
        "--wgf",
        type=str,
        default="det",
        choices=["det", "enkf", "ens", "firewx"],
        help="The working group function",
    )


def add_time_window_args(parser):
    # Some of these are used for the time series plots
    parser.add_argument(
        "--start-date",
        type=str,
        required=False,
        help="The date and UTC time that you want to start at. Ex: 2024050523",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        required=False,
        help="The date and UTC time that you want to end at. Ex: 2024050623",
    )

    parser.add_argument(
        "--lookback-hours",
        type=int,
        required=False,
        help="Number of hours to look backwards.",
    )


def get_args_obs_map():
    """
    For use with the OmB map script
    """

    parser = argparse.ArgumentParser(
        description="Plot observation-minus-background values")

    add_common_args(parser)
    add_time_window_args(parser)

    parser.add_argument(
        "--qc-flag",
        type=int,
        required=True,
        choices=[0, 1, 2],
        help="Choose between 0, 1, and 2",
    )

    parser.add_argument(
        "--qc-cycle",
        type=int,
        required=True,
        choices=[0, 1, 2],
        help="0 (before outer loop), 1 (after one pass of outer loop), 2 (after two passes of outer loop)",
    )

    parser.add_argument(
        "--bias-correction",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether or not to perform bias correction. True by default.",
    )

    parser.add_argument(
        "--show-netcdf-attributes",
        action="store_true",
        default=False,
        help="Whether or not to print out information on the NetCDF files.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Whether or not to print out helpful information for debugging.",
    )

    parser.add_argument(
        "--channel",
        type=int,
        required=True,
        help="",
    )

    parser.add_argument(
        "--observer", type=str, required=True, help="e.g. cris-fsr_n20"
    )

    final_args = parser.parse_args()
    if final_args.start_date is None:
        parser.error("--start-date is required for observation maps")

    return final_args


def get_args_single_observer_timeseries():
    parser = argparse.ArgumentParser(
        description="Plot observation counts by hour for a given list of channels")

    add_common_args(parser)
    add_time_window_args(parser)

    parser.add_argument(
        "--observer",
        type=str,
        required=True,
        help="The name of the observer (e.g. 'cris-fsr_n20)"
    )

    parser.add_argument(
        "--channels",
        nargs="+",
        type=int,
        required=True,
        help="Channel number(s). Ex: 1 2 3 4",
    )
    return parser.parse_args()


def get_args_obs_counts_multi_observer_timeseries():
    parser = argparse.ArgumentParser(
        description="Plot observation counts by hour for different observers, grouped by instruments.")

    add_common_args(parser)
    add_time_window_args(parser)

    return parser.parse_args()
