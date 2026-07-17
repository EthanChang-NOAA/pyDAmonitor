#
# import ioda
import cartopy.feature as cfeature
import netCDF4 as nc
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")


if os.environ.get('LIBDIR') is not None:
    sys.path.append(os.environ['LIBDIR'])


# Set input and output file names
# --------------------------------


fname = "jdiag_cris-fsr_n20.nc"

print("checking fname = ", fname)

# Read input data file
# ----------------------
ncd = nc.Dataset(fname, 'r')

# NetCDF global attributes
# --------------------------
nc_attrs = ncd.ncattrs()
print('NetCDF Global Attributes: ')
print('nc_attrs = ', nc_attrs)
for nc_attr in nc_attrs:
    print('nc_attr', ncd.getncattr(nc_attr))

# Dimension shape information
# -----------------------------
nc_dims = [dim for dim in ncd.dimensions]  # list of nc dimensions
print('nc_dims = ', nc_dims)
for dim in nc_dims:
    print('nc_dims', dim, len(ncd.dimensions[dim]))

# read in data
# ---------------------
latData = ncd.groups['MetaData'].variables['latitude'][:].ravel()
lonData = ncd.groups['MetaData'].variables['longitude'][:].ravel()
# satidData = ncd.groups['MetaData'].variables['satelliteId'][:].ravel()
# tbData = ncd.groups['ObsValue'].variables['brightnessTemperature'][:]
dateTime = ncd.groups['MetaData'].variables['dateTime'][:]

ombg = ncd.groups['ombg'].variables['brightnessTemperature'][:]
ObsBias0 = ncd.groups['ObsBias0'].variables['brightnessTemperature'][:]
ombnbcData = ombg + ObsBias0

DerivedObsValue = ncd.groups['DerivedObsValue'].variables['brightnessTemperature'][:]
qcflag0 = ncd.groups['EffectiveQC0'].variables['brightnessTemperature'][:]


channels = ncd.variables['Channel'][:]


# Check data
# -----------
print('dateTime = ', dateTime)
print('ombg,length=', len(ombg))
print('ombg shape = ', ombg.shape)
print(list(ncd.groups))

# domain set up
conus_12km = [-150, -50, 15, 55]

# Output directory
output_dir1 = "./CrIS_O-B_assimilated_after_BC"
output_dir2 = "./CrIS_O-B_assimilated_before_BC"
output_dir3 = "./CrIS_assimilated_HofX"
os.makedirs(output_dir1, exist_ok=True)
os.makedirs(output_dir2, exist_ok=True)
os.makedirs(output_dir3, exist_ok=True)

variables = ['O-B after BC', 'O-B before BC', 'HofX']
# variables=['O-B before BC','O-B after BC' ]
# variables=['HofX']

for variable in variables:
    print(variable)

    for i, ch in enumerate(channels):
        valid = qcflag0[:, i] == 0
        O_B_after_BC = ombg[valid, i]
        O_B_before_BC = ombnbcData[valid, i]
        obs = DerivedObsValue[valid, i]

        if O_B_after_BC.size == 0:
            continue

        lon = lonData[valid]
        lat = latData[valid]
        data_count = np.ma.count(O_B_after_BC)
        if variable == 'O-B after BC':
            obarray = O_B_after_BC
            output_dir = output_dir1
        elif variable == 'O-B before BC':
            obarray = O_B_before_BC
            output_dir = output_dir2
        elif variable == 'HofX':
            obarray = obs - O_B_before_BC
            output_dir = output_dir3
        stdev = np.nanstd(obarray)  # Standard deviation
        omean = np.nanmean(obarray)  # Mean of the data
        datamin = np.nanmin(obarray)  # Min of the data
        datamax = np.nanmax(obarray)  # Max of the data
        datcount = np.ma.count(obarray)

        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))

        # Plot grid lines
        # ----------------
        gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=0), draw_labels=True,
                          linewidth=1, color='gray', alpha=0.5, linestyle='-')
        gl.top_labels = False
        gl.xlabel_style = {'size': 10, 'color': 'black'}
        gl.ylabel_style = {'size': 10, 'color': 'black'}
        gl.xlocator = mticker.FixedLocator(
            [-180, -135, -90, -45, 0, 45, 90, 135, 179.9])

        if variable in ('O-B after BC', 'O-B before BC'):
            cmin = -3
            cmax = 3
        elif variable == 'HofX':
            cmin = datamin
            cmax = datamax

        cmap = 'jet'
        units = 'K'

        print(data_count)
        sc = ax.scatter(
            lon,
            lat,
            c=obarray,
            s=4,
            linewidth=0,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            vmin=cmin,
            vmax=cmax,
            norm=None,
            antialiased=True,
        )
        if variable in ('O-B after BC', 'O-B before BC'):
            cbar = plt.colorbar(
                sc,
                ax=ax,
                orientation="horizontal",
                pad=.1,
                fraction=0.06,
                ticks=[-3, -2.5, -2, -1.5, -1, -0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3],
            )
        elif variable == 'HofX':
            cbar = plt.colorbar(sc, ax=ax, orientation="horizontal", pad=.1, fraction=0.06)
        text = f"Total Count:{datcount:0.0f}, Max/Min/Mean/Std: {datamax:0.3f}/{datamin:0.3f}/{omean:0.3f}/{stdev:0.3f} {units}"
        print(text)
        ax.text(0.23, -0.12, text, transform=ax.transAxes, va='bottom', fontsize=8.0)
        cbar.ax.set_ylabel(units, fontsize=10)

        # plt.legend(fontsize=6)
        plt.title(f"JEDI: CrIS-FSR {variable} for Channel {int(ch)}")

        # --------------
        # ax.set_global()
        # ax.set_extent(conus)
        ax.set_extent(conus_12km)

        # Draw coastlines
        # ----------------
        ax.coastlines()
        ax.add_feature(cfeature.STATES, linewidth=0.5)

        save_path = os.path.join(output_dir, f"CrIS-FSR {variable} for_channel_{int(ch)}.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_path}")
