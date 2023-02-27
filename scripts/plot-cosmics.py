def main():
    fig, ax = plt.subplots()

    ax.plot(
        time.datetime,
        cosmics_rate,
        ".",
    )
    n_sig = config.cosmics_sigma
    ax.set_xlim(ax.get_xlim())
    ax.fill_between(
        ax.get_xlim(),
        *bounds_std(cosmics_rate, n_sig),
        alpha=0.1,
        label=f"{n_sig} sigma mean",
    )
    ax.fill_between(
        ax.get_xlim(),
        *bounds_mad(cosmics_rate, n_sig),
        alpha=0.1,
        label=f"{n_sig} sigma median",
    )
    print(f"Bounds for cosmics: {bounds_std(cosmics_rate, n_sig)}")

    ax.set_xlabel("Time")
    ax.set_ylabel("Rate / 1/s")
    ax.tick_params(axis="x", rotation=30)

    ax.legend()

    fig.savefig(outdir / f"{config.source}_cosmics_rate.pdf")
