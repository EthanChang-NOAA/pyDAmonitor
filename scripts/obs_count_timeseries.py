#!/usr/bin/env python
# compute the summary in the past 7 days, 30 days
#
import os
import sys
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

# list of observers to plot, add new ones accordingly
observers = [
    # CONVENTIONAL
    # adpsfc ----
    'adpsfc_t181', 'adpsfc_t183', 'adpsfc_t187', 'adpsfc_q181', 'adpsfc_q183', 'adpsfc_q187',
    'adpsfc_ps181', 'adpsfc_ps187', 'adpsfc_uv281', 'adpsfc_uv284', 'adpsfc_uv287',
    # adpupa ----
    'adpupa_t120', 'adpupa_q120', 'adpupa_ps120', 'adpupa_uv220',
    # aircar ----
    'aircar_t133', 'aircar_q133', 'aircar_uv233',
    # sfcshp ----
    'sfcshp_t180', 'sfcshp_t183', 'sfcshp_q180', 'sfcshp_q183',
    'sfcshp_ps180', 'sfcshp_uv280', 'sfcshp_uv282', 'sfcshp_uv284',
    # reflectivity ----
    'refl10cm',

    # SATELLITE
    # CrIS (Cross-track Infrared Sounder)
    'cris-fsr_n20', 'cris-fsr_n21',
    # ATMS (Advanced Technology Microwave Sounder (ATMS))
    'atms_npp', 'atms_n20', 'atms_n21',
    # ABI (Advanced Baseline Imager)
    'abi_g16', 'abi_g18'
]


# How the group names should appear on the time series plot
GROUP_DISPLAY_NAMES = {
    # Radiance
    "atms": "ATMS",
    "cris": "CrIS",
    "abi": "ABI",

    # Conventional
    "adpupa": "ADPUPA",
    "aircar": "AIRCAR",
    "adpsfc_t": "ADPSFC (t)",
    "adpsfc_q": "ADPSFC (q)",
    "adpsfc_uv": "ADPSFC (u, v)",
    "adpsfc_ps": "ADPSFC (ps)",
    "sfcshp": "SFCSHP"
}

# How the observer names should appear in each group.
OBSERVER_DISPLAY_NAMES = {
    "atms_n20": "ATMS_N20",
    "atms_n21": "ATMS_N21",
    "atms_npp": "ATMS_NPP",
    "cris-fsr_n20": "CrIS-FSR_N20",
    "cris-fsr_n21": "CrIS-FSR_N21",
    "abi_g16": "ABI_G16",
    "abi_g18": "ABI_G18",
}

obs_counts = ['n_ioda', 'nobs', 'nobs_r', 'n_loop1', 'n_loop2']


def read_obs_counts(CDATE: str, lookback_hours: int):
    """
    Args:
        CDATE (str): The time and date (in UTC) to end on
        lookback_hours (int): The amount of hours preceding CDATE that will be displayed in the time series.
    """
    dateEnd = datetime.strptime(CDATE, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    dateBgn = dateEnd - timedelta(hours=lookback_hours)
    MY_COM_BASE = os.getenv('MY_COM_BASE', 'MY_COM_BASE_not_defined')
    WGF = os.getenv('WGF', 'WGF_not_defined')
    RUN = os.getenv('RUN', 'RUN_not_defined')
    #
    # set default values to np.nan for each cycle
    tseries = {
        obs: {key: [np.nan] * (lookback_hours + 1) for key in obs_counts} for obs in observers
    }
    for i in range(lookback_hours+1):
        dateCur = dateBgn + timedelta(hours=i)
        PDY = datetime.strftime(dateCur, "%Y%m%d")
        cyc = datetime.strftime(dateCur, "%H")
        mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/obs_count.txt'
        if not os.path.exists(mypath):
            mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/web/obs_count.txt'
        if os.path.exists(mypath):
            # read all lines of obs_counts.txt
            all_lines = []
            with open(mypath, 'r') as infile:
                for line in infile:
                    if line.strip():
                        all_lines.append(line.strip())
            # update corresponding observers
            for j in range(1, len(all_lines)):
                segments = all_lines[j].split()
                obs = segments[0].strip()
                if obs in tseries:
                    tseries[obs]['n_ioda'][i] = float(segments[1])
                    tseries[obs]['nobs'][i] = float(segments[2])
                    tseries[obs]['nobs_r'][i] = float(segments[3])
                    tseries[obs]['n_loop1'][i] = float(segments[4])
                    tseries[obs]['n_loop2'][i] = float(segments[5])
                else:
                    print(f'"{obs}" is NOT in the observers list')
    # ~~~~~~~~~~~~~~~~~~
    return dateBgn, tseries


def read_nonvar_cld_obs_counts(CDATE, lookback_hours):
    """
    Read nonvar cloud analysis obs counts from nonvar_cloud_out.txt files.

    Parameters
    ----------
    CDATE : string
        Current cycle in YYYYMMDDHH format
    lookback_hours : integer
        Number of hours to look back for the time series

    Returns
    -------
    dateBgn : datetime
        Start of the time series
    tseries  : dict
        Nested dictionary with obs counts for each group and subtype
    """
    dateEnd = datetime.strptime(CDATE, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    dateBgn = dateEnd - timedelta(hours=lookback_hours)
    #
    # These environment variables should already be defined in the shell
    MY_COM_BASE = os.getenv('MY_COM_BASE', 'MY_COM_BASE_not_defined')
    WGF = os.getenv('WGF', 'WGF_not_defined')
    RUN = os.getenv('RUN', 'RUN_not_defined')
    #
    # set default values to np.nan for each cycle
    tseries = {
        'nonvar_satellite': {'GOES_EAST': [np.nan] * (lookback_hours + 1),
                             'GOES_WEST': [np.nan] * (lookback_hours + 1)},
        'nonvar_metar': {'raw_METAR': [np.nan] * (lookback_hours + 1)},
        'nonvar_lightning': {'raw_lightning': [np.nan] * (lookback_hours + 1)},
        'nonvar_refl': {'max_val': [np.nan] * (lookback_hours + 1)}
    }
    #
    # Match observation with each ingest program
    obs_map = {
        'GOES_EAST': 'nonvar_satellite',
        'GOES_WEST': 'nonvar_satellite',
        'raw_METAR': 'nonvar_metar',
        'raw_lightning': 'nonvar_lightning',
        'max_val': 'nonvar_refl'
    }
    #
    # Loop over each cycle
    for i in range(lookback_hours+1):
        dateCur = dateBgn + timedelta(hours=i)
        PDY = datetime.strftime(dateCur, "%Y%m%d")
        cyc = datetime.strftime(dateCur, "%H")
        mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/nonvar_cloud_out.txt'
        if not os.path.exists(mypath):
            mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/web/nonvar_cloud_out.txt'
        if os.path.exists(mypath):
            # read all lines of nonvar_cloud_out.txt
            all_lines = []
            with open(mypath, 'r') as infile:
                for line in infile:
                    if line.strip():
                        all_lines.append(line.strip())
            # extract fields from nonvar cloud analysis output file
            for j in range(1, len(all_lines)):
                obs = all_lines[j].split()[1].strip()
                for key in obs_map:
                    if obs == key:
                        group = obs_map[key]
                        tseries[group][obs][i] = all_lines[j].split()[2].strip()
                        break
    #
    # Rename refl max_val field
    tseries['nonvar_refl']['max_dbz_val'] = tseries['nonvar_refl'].pop('max_val')
    # ~~~~~~~~~~~~~~~~~~
    return dateBgn, tseries


def plot_tseries(tseries: dict, group: str, start_time: datetime, source: str = 'jedi', use_symlog: bool = False, output_file: str | None = None):
    """
    Plot time series for all subtypes in a group.

    Parameters
    ----------
    tseries     : dict  — the full tseries dictionary
    group       : str   — prefix to filter on, e.g. 'adpsfc'
    start_time  : datetime — start of the time window, e.g. '2024-01-01'
    source     : str — data source. Options: 'jedi' or 'nonvar'
    use_symlog : bool — whether or not to use a symmetric logarithmic scale (useful when the total number of observations is much larger than the number of actually assimilated observations)
    output_file : str or None — if given, save figure to this path
    """
    # --- filter observers belonging to this group ---
    subtypes = [k for k in tseries if k.startswith(group)]
    if not subtypes:
        raise ValueError(f"No observers found with prefix '{group}'")

    n_panels = len(subtypes)
    # vars_to_plot = ['nobs', 'nobs_r', 'n_loop1', 'n_loop2']
    # colors       = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    # linestyles   = ['-',       '--',       '-.',       ':']
    if source == 'jedi':
        vars_to_plot = ['nobs_r', 'n_loop1', 'n_loop2']
    elif source == 'nonvar':
        vars_to_plot = list(tseries[subtypes[0]].keys())
    else:
        raise ValueError(f"Unknown source: '{source}'")
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    linestyles = ['-',       '--',       '-.']

    # --- build time axis ---
    first_obs = subtypes[0]
    N = len(tseries[first_obs][vars_to_plot[0]])
    end_time = start_time + timedelta(hours=N - 1)
    time_index = pd.date_range(start=start_time, periods=N, freq='h')

    # --- layout ---
    fig, axes = plt.subplots(
        nrows=n_panels, ncols=1,
        figsize=(15, 2.8 * n_panels),
        sharex=True
    )
    if n_panels == 1:
        axes = [axes]   # keep iterable

    for ax, obs in zip(axes, subtypes):
        d = tseries[obs]
        has_data = False

        for var, color, ls in zip(vars_to_plot, colors, linestyles):
            y = np.array(d[var], dtype=float)   # NaN-safe cast
            if not np.all(np.isnan(y)):          # skip fully-empty series
                ax.plot(time_index, y,
                        label=var, color=color, linestyle=ls,
                        linewidth=1.2, alpha=0.85)
                has_data = True

        # Calculate total obs in period and place it under the observer name
        if has_data and source == 'jedi':
            keys = sorted(k for k in d if k.startswith('n_loop')) + ['nobs_r']
            totals = {k: np.nansum(np.array(d[k], dtype=float)) for k in keys}
            ax.text(0.01, 0.91,
                    "\n".join(f"{k}: {v:,.0f}" for k, v in totals.items()),
                    transform=ax.transAxes, fontsize=5, va='top', ha='left')

        proper_observer_name = OBSERVER_DISPLAY_NAMES.get(obs, obs)  # Falls back to its "raw" name if not present in dict
        ax.text(0.01, 0.97, proper_observer_name, transform=ax.transAxes, fontsize=8, rotation=0, va='top', ha='left')
        ax.tick_params(axis='both', labelsize=8)
        ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.5)

        if use_symlog:  # Use for any observers where nobs_r >> assimilated counts
            ax.set_yscale('symlog')  # symlog handles cycles where obs counts are 0

        if not has_data:
            ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes,
                    ha='center', va='center', color='gray', fontsize=9)

    # --- x-axis formatting (shared) ---
    # every 6 hours, labeled with date+hour
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%d\n%H'))
    # minor ticks every hour (unlabeled tick marks only)
    axes[-1].xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    # # plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=30, ha='right')
    for ax in axes:
        ax.tick_params(labelbottom=True)
        # --- y-axis formatting ---
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}"))
        if not use_symlog:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # --- single shared legend at the top ---
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
               loc='upper right', ncol=len(vars_to_plot),
               fontsize=9, framealpha=0.8)

    # Title, subtitle
    title_range = (
        f"{start_time.strftime('%Y-%m-%d %HZ')} – "
        f"{end_time.strftime('%Y-%m-%d %HZ')}"
    )

    proper_group_name = GROUP_DISPLAY_NAMES.get(group, group)

    fig.suptitle(
        f"{proper_group_name} Assimilated Observation Counts\n{title_range}",
        fontsize=13, fontweight='bold', x=0.4, y=1.002)

    fig.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved → {output_file}")
        plt.close(fig)
    else:
        plt.show()

    return fig


#
# ***********************************************************************
# !!  MAIN starts here !!
# ***********************************************************************
if __name__ == '__main__':
    args = sys.argv
    nargs = len(args) - 1
    if nargs < 2 or len(sys.argv[1]) < 10:
        print(f'Usage: {os.path.basename(sys.argv[0])} <YYYYMMDDHH> <days>')
        sys.exit(1)
    # ~~~~~~
    CDATE = sys.argv[1]
    MAX_DAYS = sys.argv[2]
    lookback_hours = int(MAX_DAYS) * 24  # days * 24 hours
    #
    # JEDI obs
    dateBgn, tseries = read_obs_counts(CDATE, lookback_hours)
    plot_tseries(tseries, group='adpsfc_t', start_time=dateBgn, output_file='obs_count_tseries_adpsfc_t.png')
    plot_tseries(tseries, group='adpsfc_q', start_time=dateBgn, output_file='obs_count_tseries_adpsfc_q.png')
    plot_tseries(tseries, group='adpsfc_uv', start_time=dateBgn, output_file='obs_count_tseries_adpsfc_uv.png')
    plot_tseries(tseries, group='adpsfc_ps', start_time=dateBgn, output_file='obs_count_tseries_adpsfc_ps.png')

    plot_tseries(tseries, group='adpupa', start_time=dateBgn, output_file='obs_count_tseries_adpupa.png')
    plot_tseries(tseries, group='aircar', start_time=dateBgn, output_file='obs_count_tseries_aircar.png')
    plot_tseries(tseries, group='sfcshp', start_time=dateBgn, output_file='obs_count_tseries_sfcshp.png')
    #
    # print(tseries['aircar_t133']['nobs_r'])  # for debugging only
    #
    # Radiance
    plot_tseries(tseries, group='cris', start_time=dateBgn, use_symlog=True, output_file='obs_count_tseries_cris.png')
    plot_tseries(tseries, group='atms', start_time=dateBgn, use_symlog=True, output_file='obs_count_tseries_atms.png')
    plot_tseries(tseries, group='abi', start_time=dateBgn, use_symlog=False, output_file='obs_count_tseries_abi.png')

    # Nonvar cloud analysis obs
    dateBgn, tseries = read_nonvar_cld_obs_counts(CDATE, lookback_hours)
    plot_tseries(tseries, group='nonvar_satellite', start_time=dateBgn, source='nonvar', output_file='obs_count_tseries_nonvar_satellite.png')
    plot_tseries(tseries, group='nonvar_metar', start_time=dateBgn, source='nonvar', output_file='obs_count_tseries_nonvar_metar.png')
    plot_tseries(tseries, group='nonvar_lightning', start_time=dateBgn, source='nonvar', output_file='obs_count_tseries_nonvar_lightning.png')
    plot_tseries(tseries, group='nonvar_refl', start_time=dateBgn, source='nonvar', output_file='obs_count_tseries_nonvar_refl.png')
