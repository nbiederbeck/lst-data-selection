from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pandas as pd
from astroplan.moon import moon_illumination
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_moon, get_sun
from astropy.table import Table
from astropy.time import Time
from config import Config
from matplotlib import colors
from matplotlib import pyplot as plt

parser = ArgumentParser()
parser.add_argument("input_path")
parser.add_argument("datacheck_path")
parser.add_argument("-o", "--output_path", required=True)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

outdir = Path(args.output_path).parent

config = Config.parse_file(args.config)


def get_mask(x, le=np.inf, ge=-np.inf):
    return np.logical_and(
        np.greater_equal(x, ge),
        np.less_equal(x, le),
    )


def nmad(x):
    """Normalized Median Absolute Difference.

    Similar to standard deviation, but more robust to outliers [0], [1].

    [0]: https://en.wikipedia.org/wiki/Robust_measures_of_scale
    [1]: https://en.wikipedia.org/wiki/Median_absolute_deviation

    """
    return 1.4826 * np.median(np.abs(x - np.median(x)))


def bounds_std(x, n_sig=1):
    m = np.mean(x)
    s = n_sig * np.std(x)

    return (m - s, m + s)


def bounds_mad(x, n_sig=1):
    m = np.median(x)
    s = n_sig * nmad(x)

    return (m - s, m + s)


if __name__ == "__main__":
    runs = pd.read_csv(args.input_path)

    run_ids = np.array(runs["Run ID"])

    runsummary = Table.read(args.datacheck_path)

    time = Time(runsummary["time"], format="unix", scale="utc")

    mask_time = get_mask(
        time,
        ge=Time("2020-12-12", scale="utc"),
        le=Time("2022-05-24", scale="utc"),
    )

    mask_run_id = np.in1d(np.array(runsummary["runnumber"]), run_ids)

    mask_pedestals_ok = np.isfinite(runsummary["num_pedestals"])

    # Exclude runs that are too far from source

    tel_pointing = SkyCoord(
        ra=runsummary["mean_ra"],
        dec=runsummary["mean_dec"],
    )

    # this should be 'configurable'
    source_coordinates = SkyCoord.from_name(config.source)

    separation = tel_pointing.separation(source_coordinates)

    mask_separation_low = np.isclose(
        u.Quantity(0.4, u.deg), separation, rtol=0, atol=0.15
    )

    mask = mask_pedestals_ok & mask_run_id & mask_time & mask_separation_low

    runsummary = runsummary[mask]
    time = time[mask]

    after_pedestals_run_id_time_separation = np.count_nonzero(mask)
    s = (
        "After selecting the time of the dataset used in AGN Zoo Paper, "
        "after removing runs with problems in pedestals and "
        "after selecting runs that are close to the observed target, "
        f"{after_pedestals_run_id_time_separation} runs are kept."
    )
    print(s)

    # Exclude runs with high zenith (?)
    #
    # Better later.

    # Exclude runs with high pedestal charges.  Check first for impact of moon.

    location = EarthLocation.of_site("lapalma")

    altaz = AltAz(obstime=time, location=location)

    sun = get_sun(time).transform_to(altaz)
    moon = get_moon(time, location=location).transform_to(altaz)

    moon_light = moon_illumination(time)
    moon_light[moon.alt.to_value(u.deg) < 0] = 1

    cmap = plt.cm.afmhot
    norm = colors.Normalize(0, 1)

    ped_std = runsummary["ped_charge_stddev"]

    mask_pedestal_charge = (config.pedestal_ll < ped_std) & (
        ped_std < config.pedestal_ul
    )

    mask = mask_pedestal_charge
    runsummary = runsummary[mask]
    time = time[mask]

    after_pedestal_charge = np.count_nonzero(mask)
    s = (
        "After checking for the deviation of the pedestal charges, "
        "possibly dependent on the moon elevation and illumination, "
        f"{after_pedestal_charge} runs are kept."
    )
    print(s)

    # Check cosmics rates

    cosmics_rate = runsummary["num_cosmics"] / runsummary["elapsed_time"]

    mask_cosmics = get_mask(cosmics_rate, ge=config.cosmics_ll, le=config.cosmics_ul)

    mask = mask_cosmics
    runsummary = runsummary[mask]
    time = time[mask]

    after_cosmics = np.count_nonzero(mask)
    s = (
        "After checking the rate of cosmics and selecting "
        "based on AGN Zoo Paper cuts, "
        f"{after_cosmics} runs are kept."
    )
    print(s)

    cosmics_rate_above10 = (
        cosmics_rate[mask] * runsummary["cosmics_fraction_pulses_above10"]
    )
    cosmics_rate_above30 = (
        cosmics_rate[mask] * runsummary["cosmics_fraction_pulses_above30"]
    )

    mask_above10 = get_mask(
        cosmics_rate_above10,
        *bounds_std(cosmics_rate_above10, config.cosmics_10_sigma)[::-1],
    )
    mask_above30 = get_mask(
        cosmics_rate_above30,
        *bounds_std(cosmics_rate_above30, config.cosmics_30_sigma)[::-1],
    )

    mask = mask_above10 & mask_above30
    runsummary = runsummary[mask]
    time = time[mask]

    after_cosmics_above_n = np.count_nonzero(mask)
    s = (
        "After cutting on the rate of cosmics with more than 10 p.e. "
        f"(resp. 30 p.e.) {after_cosmics_above_n} runs are kept."
    )
    print(s)

    np.array(runsummary["runnumber"])

    duration = u.Quantity(np.sum(runsummary["elapsed_time"]), u.s).to(u.h)
    s = (
        f"A selected total of {len(runsummary)} runs add to a "
        f"duration of {duration:.2f} of data."
    )
    print(s)

    mask = np.in1d(runs["Run ID"], runsummary["runnumber"])

    runs[mask].to_csv(args.output_path, index=False)
