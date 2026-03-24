
import matplotlib.pyplot as plt
import pandas as pd


# plotting
def plotting(df):
    if df.empty:
        print("No data to plot")
        return

    plot_df = df.copy()
    plot_df["duration_seconds"] = pd.to_numeric(
        plot_df["duration_seconds"], errors="coerce"
    ).fillna(0)

    summary = (
        plot_df.groupby("predicted_category")["duration_seconds"]
        .sum()
        .sort_values(ascending=False)
    )

    if summary.empty:
        print("No category data to plot")
        return

    minutes = summary / 60

    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 8))
    total_minutes = minutes.sum()
    percentages = (minutes / total_minutes) * 100 if total_minutes else minutes * 0
    labels = [
        f"{category} ({value:.1f} min)" if pct >= 5 else ""
        for category, value, pct in zip(minutes.index, minutes.values, percentages.values)
    ]

    def autopct_if_large(pct):
        return f"{pct:.1f}%" if pct >= 2 else ""

    wedges, _, _ = ax.pie(
        minutes.values,
        labels=labels,
        autopct=autopct_if_large,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
    )
    ax.set_title("Time Spent by Predicted Category", fontsize=16, fontweight="bold")
    ax.axis("equal")
    ax.legend(
        wedges,
        [f"{category} ({value:.1f} min)" for category, value in minutes.items()],
        title="Categories",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
    )

    plt.tight_layout()

    plt.show()

# get idle time vs active time for categories
def plotIdleVsActive(df):
    if df.empty:
        print("No data to plot")
        return

    plot_df = df.copy()
    plot_df["duration_seconds"] = pd.to_numeric(
        plot_df["duration_seconds"], errors="coerce"
    ).fillna(0)
    plot_df["idle_time"] = pd.to_numeric(plot_df["idle_time"], errors="coerce").fillna(0)
    plot_df["active_time"] = (plot_df["duration_seconds"] - plot_df["idle_time"]).clip(lower=0)

    summary = (
        plot_df.groupby("predicted_category")[["active_time", "idle_time"]]
        .sum()
        .sort_values("active_time", ascending=False)
        / 60
    )

    if summary.empty:
        print("No category data to plot")
        return

    ax = summary.plot(
        kind="bar",
        figsize=(10, 6),
        color=["seagreen", "salmon"],
        edgecolor="black",
    )
    ax.set_title("Idle vs Active Time by Category", fontsize=16, fontweight="bold")
    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Time (minutes)", fontsize=12)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(["Active Time", "Idle Time"])
    plt.tight_layout()
    plt.show()

# get top 5 most used apps
def plotTopApps(df):
    if df.empty:
        print("No data to plot")
        return

    plot_df = df.copy()
    plot_df["duration_seconds"] = pd.to_numeric(
        plot_df["duration_seconds"], errors="coerce"
    ).fillna(0)

    summary = (
        plot_df.groupby("app")["duration_seconds"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        / 60
    )

    if summary.empty:
        print("No app data to plot")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(summary.index[::-1], summary.values[::-1], color="cornflowerblue", edgecolor="black")
    ax.set_title("Top 5 Most Used Apps", fontsize=16, fontweight="bold")
    ax.set_xlabel("Time (minutes)", fontsize=12)
    ax.set_ylabel("App", fontsize=12)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height() / 2, f"{width:.1f}", va="center")

    plt.tight_layout()
    plt.show()
