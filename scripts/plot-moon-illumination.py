from argparse import ArgumentParser

from matplotlib import pyplot as plt

from config import Config

parser = ArgumentParser()
parser.add_argument("-o", "--output_path", required=True)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

config = Config.parse_file(args.config)


def main():
    fig, ax = plt.subplots()

    im = ax.scatter(
        moon.alt.to_value(u.deg),
        ped_std,
        label="moon",
        c=moon_light,
        cmap=cmap,
        norm=norm,
        edgecolor="k",
    )

    masked = ped_std[moon.alt.to_value(u.deg) < 0]
    n_sig = config.pedestal_sigma

    ax.set_ylim(0)
    ax.set_xlim(-90, 80)

    ax.fill_between(
        (0, 1),
        *bounds_std(masked, n_sig),
        alpha=0.1,
        label=f"{n_sig} sigma mean",
        transform=ax.get_yaxis_transform(),
    )
    ax.fill_between(
        (0, 1),
        *bounds_mad(masked, n_sig),
        alpha=0.1,
        label=f"{n_sig} sigma median",
        transform=ax.get_yaxis_transform(),
    )
    print(f"Bounds for pedestal charge std dev: {bounds_std(masked, n_sig)}")

    ax.set_ylabel("Pedestal Charge Std.Dev. / p.e.")
    ax.set_xlabel("Altitude / deg")

    fig.colorbar(im, ax=ax, label="Moon Illumination")

    ax.legend()

    fig.savefig(outdir / f"{config.source}_ped_charge_stddev.pdf")


if __name__ == "__main__":
    main()
