from argparse import ArgumentParser

from matplotlib import pyplot as plt

from config import Config

parser = ArgumentParser()
parser.add_argument("-o", "--output_path", required=True)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

config = Config.parse_file(args.config)


def main():
    fig, (ax10, ax30) = plt.subplots(nrows=2, sharex=True)

    ax10.plot(
        time.datetime,
        cosmics_rate_above10,
        ".",
        label="Pulses > 10 p.e.",
    )
    ax30.plot(
        time.datetime,
        cosmics_rate_above30,
        ".",
        label="Pulses > 30 p.e.",
    )

    ax10.set_xlim(ax10.get_xlim())
    ax30.set_xlim(ax30.get_xlim())
    ax10.fill_between(
        ax.get_xlim(),
        *bounds_std(cosmics_rate_above10, config.cosmics_10_sigma),
        alpha=0.1,
        label=f"{config.cosmics_10_sigma} sigma mean",
    )
    ax30.fill_between(
        ax.get_xlim(),
        *bounds_std(cosmics_rate_above30, config.cosmics_30_sigma),
        alpha=0.1,
        label=f"{config.cosmics_30_sigma} sigma mean",
    )
    print(
        "Bounds for cosmics above 10: "
        f"{bounds_std(cosmics_rate_above10, config.cosmics_10_sigma)}"
    )
    print(
        "Bounds for cosmics above 30: "
        f"{bounds_std(cosmics_rate_above30, config.cosmics_30_sigma)}"
    )

    ax10.legend()
    ax30.legend()

    ax30.set_xlabel("Time")

    ax10.set_ylabel("Rate / 1/s")
    ax30.set_ylabel("Rate / 1/s")

    ax30.tick_params(axis="x", rotation=30)

    fig.savefig(outdir / f"{config.source}_cosmics_pulses_above.pdf")


if __name__ == "__main__":
    main()
