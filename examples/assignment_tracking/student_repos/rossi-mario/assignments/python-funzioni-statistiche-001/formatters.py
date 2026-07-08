def format_summary(summary):
    return (
        f"n={summary['count']} "
        f"min={summary['minimum']:.0f} "
        f"max={summary['maximum']:.0f} "
        f"avg={summary['average']:.2f}"
    )
