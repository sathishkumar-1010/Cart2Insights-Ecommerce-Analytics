
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector

from database import get_connection, run_query
from utils import show_bar_chart, show_pie_chart
import queries


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Cart2Insights | E-Commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

sns.set_theme(style="whitegrid")

st.title("🛒 Cart2Insights: Decoding E-Commerce Performance")
st.caption(
    "An interactive dashboard for sales, customers, products, "
    "sellers, deliveries, and customer experience."
)


# =========================================================
# 2. DATABASE CONNECTION
# =========================================================

try:
    conn = get_connection()

    if not conn.is_connected():
        st.error("Unable to connect to MySQL.")
        st.stop()

    # =====================================================
    # 3. BUSINESS OVERVIEW
    # =====================================================

    st.header("1. Business Overview")

    overview = run_query(
        queries.BUSINESS_OVERVIEW_QUERY
    ).iloc[0]

    total_orders = int(overview["total_orders"])
    total_customers = int(overview["total_customers"])
    total_sellers = int(overview["total_sellers"])
    total_revenue = float(overview["total_revenue"] or 0)

    avg_review = (
        float(overview["avg_review_score"])
        if pd.notna(overview["avg_review_score"])
        else 0
    )

    avg_order_value = (
        total_revenue / total_orders if total_orders else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Total Customer Records", f"{total_customers:,}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Total Sellers", f"{total_sellers:,}")
    c5.metric("Average Order Value", f"₹{avg_order_value:,.2f}")
    c6.metric("Average Review Score", f"{avg_review:.2f} / 5")

    st.caption(
        "Revenue is item price plus freight charges, not net profit. "
        "Customer records may include multiple records for the same unique customer."
    )

    st.divider()

    # =====================================================
    # 4. ORDER ANALYSIS
    # =====================================================

    st.header("2. Order Analysis")

    left, right = st.columns(2)

    with left:
        st.subheader("Order Status Distribution")

        order_status = run_query(
            queries.ORDER_STATUS_QUERY
        )

        show_bar_chart(
            order_status,
            "order_count",
            "order_status",
            "Orders by Status",
            "Number of Orders",
            "Order Status"
        )

    with right:
        st.subheader("Payment Type Distribution")

        payment_types = run_query(
            queries.PAYMENT_TYPE_QUERY
        )

        show_bar_chart(
            payment_types,
            "payment_count",
            "payment_type",
            "Payment Methods",
            "Number of Payment Records",
            "Payment Method",
            figsize=(8, 5)
        )

    st.divider()

    # =====================================================
    # 5. SALES ANALYSIS
    # =====================================================

    st.header("3. Sales Analysis")

    st.subheader("Monthly Revenue Trend")

    monthly_revenue = run_query(
        queries.MONTHLY_REVENUE_QUERY
    )

    if not monthly_revenue.empty:
        monthly_revenue["month"] = pd.to_datetime(
            monthly_revenue["month"], format="%Y-%m"
        )

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(
            monthly_revenue["month"],
            monthly_revenue["revenue"],
            marker="o"
        )
        ax.set_title("Monthly Revenue Trend")
        ax.set_xlabel("Month")
        ax.set_ylabel("Item Price + Freight (₹)")
        ax.ticklabel_format(axis="y", style="plain")
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "The final month may contain incomplete data, "
            "so check it before interpreting a decline."
        )

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Categories by Revenue")

        category_revenue = run_query(
            queries.TOP_CATEGORIES_QUERY
        )

        show_bar_chart(
            category_revenue,
            "revenue",
            "category",
            "Top Categories by Revenue",
            "Revenue (₹)",
            "Category"
        )

    with right:
        st.subheader("Top 10 Selling Products")

        top_products = run_query(
            queries.TOP_PRODUCTS_QUERY
        )

        if not top_products.empty:
            top_products["product_id"] = (
                top_products["product_id"]
                .astype(str)
                .str.slice(0, 12)
            )

        show_bar_chart(
            top_products,
            "units_sold",
            "product_id",
            "Top Products by Order-Item Records",
            "Order-Item Records",
            "Product ID"
        )

    st.subheader("Top 10 Customer Cities by Sales")

    city_sales = run_query(
        queries.CITY_SALES_QUERY
    )

    show_bar_chart(
        city_sales,
        "sales",
        "city",
        "Top Customer Cities by Sales",
        "Sales (₹)",
        "City"
    )

    st.divider()

    # =====================================================
    # 6. CUSTOMER ANALYSIS
    # =====================================================

    st.header("4. Customer Analysis")

    left, right = st.columns(2)

    with left:
        st.subheader("Customer Distribution by State")

        state_customers = run_query(
            queries.CUSTOMER_STATE_QUERY
        )

        show_bar_chart(
            state_customers,
            "customers",
            "state",
            "Unique Customers by State",
            "Unique Customers",
            "State"
        )

    with right:
        st.subheader("Customer Spending Distribution")

        customer_spending = run_query(
            queries.CUSTOMER_SPENDING_QUERY
        )

        if not customer_spending.empty:
            fig, ax = plt.subplots(figsize=(9, 5))
            sns.histplot(
                data=customer_spending,
                x="total_spending",
                bins=50,
                ax=ax
            )
            ax.set_title("Customer Spending Distribution")
            ax.set_xlabel("Total Spending (₹)")
            ax.set_ylabel("Number of Unique Customers")
            ax.set_xlim(left=0)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    left, right = st.columns(2)

    with left:
        st.subheader("Repeat vs One-Time Customers")

        customer_frequency = run_query(
            queries.CUSTOMER_FREQUENCY_QUERY
        )

        if not customer_frequency.empty:
            customer_frequency["customer_type"] = (
                customer_frequency["order_count"].apply(
                    lambda n: "Repeat Customer"
                    if n > 1 else "One-Time Customer"
                )
            )

            customer_types = (
                customer_frequency["customer_type"]
                .value_counts()
                .rename_axis("customer_type")
                .reset_index(name="customer_count")
            )

            show_pie_chart(
                customer_types,
                "customer_count",
                "customer_type",
                "Repeat vs One-Time Customers"
            )

    with right:
        st.subheader("Top 10 Customers by Spending")

        if not customer_spending.empty:
            top_customers = customer_spending.nlargest(
                10, "total_spending"
            ).copy()

            top_customers["customer_unique_id"] = (
                top_customers["customer_unique_id"]
                .astype(str)
                .str.slice(0, 12)
            )

            show_bar_chart(
                top_customers,
                "total_spending",
                "customer_unique_id",
                "Top Customers by Spending",
                "Total Spending (₹)",
                "Customer ID"
            )

    st.divider()

    # =====================================================
    # 7. SELLER & PRODUCT ANALYSIS
    # =====================================================

    st.header("5. Seller & Product Analysis")

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Sellers by Orders Handled")

        seller_orders = run_query(
            queries.SELLER_ORDERS_QUERY
        )

        if not seller_orders.empty:
            seller_orders["seller_id"] = (
                seller_orders["seller_id"]
                .astype(str)
                .str.slice(0, 12)
            )

        show_bar_chart(
            seller_orders,
            "orders_handled",
            "seller_id",
            "Top Sellers by Orders",
            "Orders Handled",
            "Seller ID"
        )

    with right:
        st.subheader("Top 10 Sellers by Revenue")

        seller_revenue = run_query(
            queries.SELLER_REVENUE_QUERY
        )

        if not seller_revenue.empty:
            seller_revenue["seller_id"] = (
                seller_revenue["seller_id"]
                .astype(str)
                .str.slice(0, 12)
            )

        show_bar_chart(
            seller_revenue,
            "revenue",
            "seller_id",
            "Top Sellers by Revenue",
            "Revenue (₹)",
            "Seller ID"
        )

    left, right = st.columns(2)

    with left:
        st.subheader("Product Category Performance")

        category_units = run_query(
            queries.CATEGORY_UNITS_QUERY
        )

        show_bar_chart(
            category_units,
            "items_sold",
            "category",
            "Top Categories by Items Sold",
            "Items Sold",
            "Category"
        )

    with right:
        st.subheader("Top Sellers by Average Review Score")

        seller_reviews = run_query(
            queries.SELLER_REVIEWS_QUERY
        )

        if not seller_reviews.empty:
            seller_reviews["seller_id"] = (
                seller_reviews["seller_id"]
                .astype(str)
                .str.slice(0, 12)
            )

        show_bar_chart(
            seller_reviews,
            "avg_review_score",
            "seller_id",
            "Top Sellers by Average Review",
            "Average Review Score",
            "Seller ID"
        )

    st.divider()

    # =====================================================
    # 8. DELIVERY ANALYSIS
    # =====================================================

    st.header("6. Delivery Analysis")

    delivery_time = run_query(
        queries.DELIVERY_TIME_QUERY
    ).iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Average Delivery Time",
        f"{delivery_time['avg_days']:.2f} days"
        if pd.notna(delivery_time["avg_days"]) else "N/A"
    )

    c2.metric(
        "Shortest Delivery Time",
        f"{delivery_time['min_days']:.2f} days"
        if pd.notna(delivery_time["min_days"]) else "N/A"
    )

    c3.metric(
        "Longest Delivery Time",
        f"{delivery_time['max_days']:.2f} days"
        if pd.notna(delivery_time["max_days"]) else "N/A"
    )

    st.subheader("On-Time/Early vs Delayed Orders")

    delivery_status = run_query(
        queries.DELIVERY_STATUS_QUERY
    )

    if not delivery_status.empty:
        left, right = st.columns(2)

        with left:
            show_pie_chart(
                delivery_status,
                "order_count",
                "delivery_status",
                "Delivery Status Breakdown"
            )

        with right:
            st.dataframe(
                delivery_status.rename(
                    columns={
                        "delivery_status": "Delivery Status",
                        "order_count": "Orders"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

    st.subheader("Average Delivery Time by Customer State")

    delivery_by_state = run_query(
        queries.DELIVERY_BY_STATE_QUERY
    )

    show_bar_chart(
        delivery_by_state,
        "avg_delivery_days",
        "state",
        "Average Delivery Days by State",
        "Average Delivery Days",
        "Customer State"
    )

    if not delivery_by_state.empty:
        with st.expander("View delivery performance data"):
            st.dataframe(
                delivery_by_state.rename(
                    columns={
                        "state": "State",
                        "delivered_orders": "Delivered Orders",
                        "avg_delivery_days": "Average Delivery Days"
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True
            )

    st.subheader("Delivery Delay vs Customer Review Score")

    delay_review = run_query(
        queries.DELIVERY_DELAY_REVIEW_QUERY
    )

    if not delay_review.empty:
        show_bar_chart(
            delay_review,
            "avg_review_score",
            "delivery_bucket",
            "Average Review Score by Delivery Timing",
            "Average Review Score",
            "Delivery Timing"
        )

        with st.expander("View review scores by delivery timing"):
            st.dataframe(
                delay_review[
                    ["delivery_bucket", "avg_review_score", "review_count"]
                ].rename(
                    columns={
                        "delivery_bucket": "Delivery Timing",
                        "avg_review_score": "Average Review Score",
                        "review_count": "Reviews"
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True
            )

    st.caption(
        "Delivery time measures purchase-to-delivery duration. "
        "An association between delivery timing and ratings does not "
        "by itself establish causation."
    )

    st.divider()

    # =====================================================
    # 9. CUSTOMER EXPERIENCE
    # =====================================================

    st.header("7. Customer Experience")

    st.subheader("Review Score Distribution")

    review_distribution = run_query(
        queries.REVIEW_DISTRIBUTION_QUERY
    )

    if not review_distribution.empty:
        fig, ax = plt.subplots(figsize=(9, 5))

        sns.barplot(
            data=review_distribution,
            x="review_score",
            y="review_count",
            color="steelblue",
            ax=ax
        )

        ax.set_title("Customer Review Score Distribution")
        ax.set_xlabel("Review Score")
        ax.set_ylabel("Number of Reviews")
        ax.set_xticks([0, 1, 2, 3, 4])
        ax.set_xticklabels(
            ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"]
        )

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        total_reviews = int(
            review_distribution["review_count"].sum()
        )

        five_star = int(
            review_distribution.loc[
                review_distribution["review_score"] == 5,
                "review_count"
            ].sum()
        )

        one_star = int(
            review_distribution.loc[
                review_distribution["review_score"] == 1,
                "review_count"
            ].sum()
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", f"{total_reviews:,}")

        c2.metric(
            "5-Star Reviews",
            f"{five_star:,}",
            f"{five_star / total_reviews * 100:.1f}%"
            if total_reviews else None
        )

        c3.metric(
            "1-Star Reviews",
            f"{one_star:,}",
            f"{one_star / total_reviews * 100:.1f}%"
            if total_reviews else None
        )

    st.subheader("Average Review Score by Product Category")

    category_reviews = run_query(
        queries.CATEGORY_REVIEWS_QUERY
    )

    if not category_reviews.empty:
        rating_view = st.radio(
            "Category ranking",
            ["Highest Rated", "Lowest Rated"],
            horizontal=True
        )

        if rating_view == "Highest Rated":
            shown = category_reviews.nlargest(
                10, "avg_review_score"
            ).sort_values("avg_review_score")
        else:
            shown = category_reviews.nsmallest(
                10, "avg_review_score"
            ).sort_values(
                "avg_review_score", ascending=False
            )

        show_bar_chart(
            shown,
            "avg_review_score",
            "category",
            f"{rating_view} Product Categories",
            "Average Review Score",
            "Product Category"
        )

        with st.expander("View category review data"):
            st.dataframe(
                category_reviews.rename(
                    columns={
                        "category": "Category",
                        "avg_review_score": "Average Review Score",
                        "review_count": "Reviews"
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True
            )

    st.subheader("Customer Ratings vs Delivery Time")

    delivery_rating = run_query(
        queries.DELIVERY_RATING_QUERY
    )

    if not delivery_rating.empty:
        show_bar_chart(
            delivery_rating,
            "avg_review_score",
            "delivery_time_group",
            "Average Rating by Delivery Duration",
            "Average Review Score",
            "Delivery Duration"
        )

        with st.expander("View delivery and rating data"):
            st.dataframe(
                delivery_rating[
                    [
                        "delivery_time_group",
                        "avg_review_score",
                        "review_count"
                    ]
                ].rename(
                    columns={
                        "delivery_time_group": "Delivery Duration",
                        "avg_review_score": "Average Review Score",
                        "review_count": "Reviews"
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    # =====================================================
    # 10. BUSINESS INSIGHTS & RECOMMENDATIONS
    # =====================================================

    st.header("8. Business Insights & Recommendations")

    st.markdown(
        "These insights are calculated from the current database results."
    )

    # Revenue insights
    st.subheader("Revenue Insights")

    revenue_detail = run_query(
        queries.REVENUE_BREAKDOWN_QUERY
    ).iloc[0]

    item_revenue = float(revenue_detail["item_revenue"] or 0)
    freight_revenue = float(revenue_detail["freight_revenue"] or 0)
    combined_value = item_revenue + freight_revenue

    c1, c2, c3 = st.columns(3)
    c1.metric("Item Revenue", f"₹{item_revenue:,.2f}")
    c2.metric("Freight Charges", f"₹{freight_revenue:,.2f}")
    c3.metric("Combined Value", f"₹{combined_value:,.2f}")

    if combined_value > 0:
        st.write(
            f"**Insight:** Freight charges account for "
            f"{freight_revenue / combined_value * 100:.1f}% "
            "of combined item and freight value."
        )

    if not monthly_revenue.empty:
        best_month = monthly_revenue.loc[
            monthly_revenue["revenue"].idxmax()
        ]

        st.write(
            f"**Highest-revenue month:** "
            f"{best_month['month'].strftime('%Y-%m')} with "
            f"₹{best_month['revenue']:,.2f} in combined value."
        )

    st.info(
        "**Recommendation:** Review monthly trends and freight charges "
        "together. Investigate high freight costs and assess product "
        "margins before increasing promotions."
    )

    st.divider()

    # Product category insights
    st.subheader("Product Category Insights")

    if not category_revenue.empty:
        top_category = category_revenue.iloc[0]

        most_sold_category = (
            category_units.loc[
                category_units["items_sold"].idxmax()
            ]
            if not category_units.empty
            else None
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Highest-Value Category",
            str(top_category["category"]),
            f"₹{top_category['revenue']:,.2f}"
        )

        if most_sold_category is not None:
            c2.metric(
                "Highest-Volume Category",
                str(most_sold_category["category"]),
                f"{int(most_sold_category['items_sold']):,} items"
            )

        st.info(
            "**Recommendation:** Evaluate category revenue, sales volume, "
            "margins, and customer ratings before choosing products for promotion."
        )

    st.divider()

    # Customer retention insights
    st.subheader("Customer Retention Insights")

    retention = run_query(
        queries.RETENTION_INSIGHT_QUERY
    ).iloc[0]

    unique_count = int(retention["unique_customers"] or 0)
    one_time_count = int(retention["one_time_customers"] or 0)
    repeat_count = int(retention["repeat_customers"] or 0)

    repeat_rate = (
        repeat_count / unique_count * 100 if unique_count else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Customers", f"{unique_count:,}")
    c2.metric("One-Time Customers", f"{one_time_count:,}")
    c3.metric("Repeat Customer Rate", f"{repeat_rate:.2f}%")

    st.write(
        f"**Insight:** {repeat_rate:.2f}% of unique customers "
        "in the available order history placed more than one order."
    )

    st.info(
        "**Recommendation:** Test post-purchase campaigns, loyalty benefits, "
        "and personalized product suggestions. Measure whether they improve retention."
    )

    st.divider()

    # Delivery insights
    st.subheader("Delivery Performance Insights")

    delivery_summary = run_query(
        queries.DELIVERY_INSIGHT_QUERY
    ).iloc[0]

    delivered_count = int(delivery_summary["delivered_orders"] or 0)
    delayed_count = int(delivery_summary["delayed_orders"] or 0)

    delay_rate = (
        delayed_count / delivered_count * 100
        if delivered_count else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Delivered Orders", f"{delivered_count:,}")
    c2.metric("Delayed Orders", f"{delayed_count:,}")
    c3.metric("Delayed Order Rate", f"{delay_rate:.2f}%")

    st.info(
        "**Recommendation:** Investigate delayed deliveries by state, seller, "
        "and category. Improve delivery estimates and customer notifications "
        "where the data identifies problems."
    )

    st.divider()

    # Customer satisfaction insights
    st.subheader("Customer Satisfaction Insights")

    satisfaction = run_query(
        queries.SATISFACTION_INSIGHT_QUERY
    ).iloc[0]

    review_count = int(satisfaction["total_reviews"] or 0)
    low_count = int(satisfaction["low_reviews"] or 0)
    positive_count = int(satisfaction["positive_reviews"] or 0)

    low_pct = (
        low_count / review_count * 100 if review_count else 0
    )

    positive_pct = (
        positive_count / review_count * 100 if review_count else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Reviews", f"{review_count:,}")

    c2.metric(
        "Average Review Score",
        (
            f"{float(satisfaction['avg_review_score']):.2f} / 5"
            if pd.notna(satisfaction["avg_review_score"])
            else "N/A"
        )
    )

    c3.metric("Low Ratings (1–2)", f"{low_pct:.2f}%")

    st.write(
        f"**Insight:** {positive_pct:.2f}% of reviews are 4 or 5 stars, "
        f"while {low_pct:.2f}% are 1 or 2 stars."
    )

    st.info(
        "**Recommendation:** Review low-rated orders to identify recurring "
        "issues such as delivery delays, product quality, or support. "
        "Confirm the cause before choosing corrective actions."
    )

    st.divider()

    st.subheader("Business Action Plan")

    st.markdown("""
    1. **Revenue:** Track monthly trends, item revenue, and freight costs.
    2. **Products:** Prioritize categories using revenue, sales volume,
       customer ratings, and margin data.
    3. **Retention:** Identify one-time buyers and test repeat-purchase campaigns.
    4. **Delivery:** Investigate late orders by state and seller.
    5. **Customer experience:** Analyze low reviews and validate the main
       reasons for dissatisfaction.
    """)

    st.caption(
        "All findings are descriptive. Revenue is not net profit, "
        "and correlation does not establish causation."
    )

    # =====================================================
    # FOOTER
    # =====================================================

    st.divider()

    st.caption(
        "Cart2Insights | E-Commerce Analytics Project | "
        "Data-driven business decision support"
    )

except mysql.connector.Error as error:
    st.error(f"MySQL error: {error}")
    st.info(
        "Check that MySQL is running, ecommerce_db exists, "
        "the credentials are correct, and all required tables exist."
    )

except Exception as error:
    st.error(f"An unexpected error occurred: {error}")
    st.info(
        "Copy the complete error message so the issue can be diagnosed."
    )
