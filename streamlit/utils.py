
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


def show_bar_chart(
    data,
    x,
    y,
    title,
    xlabel,
    ylabel,
    figsize=(10, 5)
):
    """Display a reusable horizontal bar chart."""

    if data.empty:
        st.info(f"No data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=figsize)

    sns.barplot(
        data=data,
        x=x,
        y=y,
        color="steelblue",
        ax=ax
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def show_pie_chart(data, values, labels, title):
    """Display a reusable pie chart."""

    if data.empty:
        st.info(f"No data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.pie(
        data[values],
        labels=data[labels],
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title(title)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)
