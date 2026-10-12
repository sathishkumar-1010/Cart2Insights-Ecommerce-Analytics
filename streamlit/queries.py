
# =========================================================
# CART2INSIGHTS - SQL QUERY DEFINITIONS
# =========================================================

# =========================================================
# 1. BUSINESS OVERVIEW
# =========================================================

BUSINESS_OVERVIEW_QUERY = """
SELECT
    (SELECT COUNT(*) FROM orders) AS total_orders,
    (SELECT COUNT(*) FROM customers) AS total_customers,
    (SELECT COUNT(*) FROM sellers) AS total_sellers,
    (SELECT COALESCE(SUM(price + freight_value), 0)
     FROM order_items) AS total_revenue,
    (SELECT AVG(review_score)
     FROM order_reviews) AS avg_review_score
"""

REVENUE_BREAKDOWN_QUERY = """
SELECT
    COALESCE(SUM(price), 0) AS item_revenue,
    COALESCE(SUM(freight_value), 0) AS freight_revenue
FROM order_items
"""


# =========================================================
# 2. ORDER ANALYSIS
# =========================================================

ORDER_STATUS_QUERY = """
SELECT
    order_status,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC
"""

PAYMENT_TYPE_QUERY = """
SELECT
    payment_type,
    COUNT(*) AS payment_count
FROM order_payments
GROUP BY payment_type
ORDER BY payment_count DESC
"""


# =========================================================
# 3. SALES ANALYSIS
# =========================================================

MONTHLY_REVENUE_QUERY = """
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
    SUM(oi.price + oi.freight_value) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_purchase_timestamp IS NOT NULL
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
ORDER BY month
"""

TOP_CATEGORIES_QUERY = """
SELECT
    COALESCE(
        pct.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,
    SUM(oi.price + oi.freight_value) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation pct
    ON p.product_category_name = pct.product_category_name
GROUP BY category
ORDER BY revenue DESC
LIMIT 10
"""

TOP_PRODUCTS_QUERY = """
SELECT
    product_id,
    COUNT(*) AS units_sold
FROM order_items
GROUP BY product_id
ORDER BY units_sold DESC
LIMIT 10
"""

CITY_SALES_QUERY = """
SELECT
    c.customer_city AS city,
    SUM(oi.price + oi.freight_value) AS sales
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE c.customer_city IS NOT NULL
GROUP BY c.customer_city
ORDER BY sales DESC
LIMIT 10
"""


# =========================================================
# 4. CUSTOMER ANALYSIS
# =========================================================

CUSTOMER_STATE_QUERY = """
SELECT
    customer_state AS state,
    COUNT(DISTINCT customer_unique_id) AS customers
FROM customers
WHERE customer_state IS NOT NULL
  AND customer_unique_id IS NOT NULL
GROUP BY customer_state
ORDER BY customers DESC
"""

CUSTOMER_SPENDING_QUERY = """
SELECT
    c.customer_unique_id,
    SUM(oi.price + oi.freight_value) AS total_spending
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE c.customer_unique_id IS NOT NULL
GROUP BY c.customer_unique_id
"""

CUSTOMER_FREQUENCY_QUERY = """
SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id) AS order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE c.customer_unique_id IS NOT NULL
GROUP BY c.customer_unique_id
"""


# =========================================================
# 5. SELLER AND PRODUCT ANALYSIS
# =========================================================

SELLER_ORDERS_QUERY = """
SELECT
    seller_id,
    COUNT(DISTINCT order_id) AS orders_handled
FROM order_items
GROUP BY seller_id
ORDER BY orders_handled DESC
LIMIT 10
"""

SELLER_REVENUE_QUERY = """
SELECT
    seller_id,
    SUM(price + freight_value) AS revenue
FROM order_items
GROUP BY seller_id
ORDER BY revenue DESC
LIMIT 10
"""

CATEGORY_UNITS_QUERY = """
SELECT
    COALESCE(
        pct.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,
    COUNT(*) AS items_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation pct
    ON p.product_category_name = pct.product_category_name
GROUP BY category
ORDER BY items_sold DESC
LIMIT 10
"""

SELLER_REVIEWS_QUERY = """
SELECT
    oi.seller_id,
    AVG(r.review_score) AS avg_review_score,
    COUNT(DISTINCT r.review_id) AS review_count
FROM order_items oi
JOIN order_reviews r ON oi.order_id = r.order_id
WHERE r.review_score BETWEEN 1 AND 5
GROUP BY oi.seller_id
HAVING COUNT(DISTINCT r.review_id) >= 10
ORDER BY avg_review_score DESC
LIMIT 10
"""


# =========================================================
# 6. DELIVERY ANALYSIS
# =========================================================

DELIVERY_TIME_QUERY = """
SELECT
    AVG(
        TIMESTAMPDIFF(
            SECOND,
            order_purchase_timestamp,
            order_delivered_customer_date
        ) / 86400.0
    ) AS avg_days,
    MIN(
        TIMESTAMPDIFF(
            SECOND,
            order_purchase_timestamp,
            order_delivered_customer_date
        ) / 86400.0
    ) AS min_days,
    MAX(
        TIMESTAMPDIFF(
            SECOND,
            order_purchase_timestamp,
            order_delivered_customer_date
        ) / 86400.0
    ) AS max_days
FROM orders
WHERE order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL
  AND order_delivered_customer_date >= order_purchase_timestamp
"""

DELIVERY_STATUS_QUERY = """
SELECT
    CASE
        WHEN order_delivered_customer_date
             <= order_estimated_delivery_date
        THEN 'On Time or Early'
        ELSE 'Delayed'
    END AS delivery_status,
    COUNT(*) AS order_count
FROM orders
WHERE order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL
GROUP BY delivery_status
"""

DELIVERY_BY_STATE_QUERY = """
SELECT
    c.customer_state AS state,
    COUNT(*) AS delivered_orders,
    AVG(
        TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0
    ) AS avg_delivery_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_purchase_timestamp IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_customer_date >= o.order_purchase_timestamp
  AND c.customer_state IS NOT NULL
GROUP BY c.customer_state
HAVING COUNT(*) >= 50
ORDER BY avg_delivery_days DESC
"""

DELIVERY_DELAY_REVIEW_QUERY = """
SELECT
    CASE
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) < -7 THEN 1
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) <= 0 THEN 2
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) <= 7 THEN 3
        ELSE 4
    END AS bucket_order,
    CASE
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) < -7 THEN 'More than 7 days early'
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) <= 0 THEN 'Up to 7 days early / on time'
        WHEN DATEDIFF(
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        ) <= 7 THEN '1-7 days late'
        ELSE 'More than 7 days late'
    END AS delivery_bucket,
    AVG(r.review_score) AS avg_review_score,
    COUNT(DISTINCT r.review_id) AS review_count
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND r.review_score BETWEEN 1 AND 5
GROUP BY bucket_order, delivery_bucket
ORDER BY bucket_order
"""

DELIVERY_RATING_QUERY = """
SELECT
    CASE
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 7 THEN 1
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 14 THEN 2
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 21 THEN 3
        ELSE 4
    END AS bucket_order,
    CASE
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 7 THEN '7 days or less'
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 14 THEN '8-14 days'
        WHEN TIMESTAMPDIFF(
            SECOND,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0 <= 21 THEN '15-21 days'
        ELSE 'More than 21 days'
    END AS delivery_time_group,
    AVG(r.review_score) AS avg_review_score,
    COUNT(DISTINCT r.review_id) AS review_count
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_purchase_timestamp IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_customer_date >= o.order_purchase_timestamp
  AND r.review_score BETWEEN 1 AND 5
GROUP BY bucket_order, delivery_time_group
ORDER BY bucket_order
"""


# =========================================================
# 7. CUSTOMER EXPERIENCE
# =========================================================

REVIEW_DISTRIBUTION_QUERY = """
SELECT
    review_score,
    COUNT(*) AS review_count
FROM order_reviews
WHERE review_score BETWEEN 1 AND 5
GROUP BY review_score
ORDER BY review_score
"""


CATEGORY_REVIEWS_QUERY = """
SELECT
    COALESCE(
        pct.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,
    AVG(r.review_score) AS avg_review_score,
    COUNT(DISTINCT r.review_id) AS review_count
FROM order_reviews r
JOIN (
    SELECT DISTINCT
        oi.order_id,
        oi.product_id
    FROM order_items oi
) AS oi ON r.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_category_translation pct
    ON p.product_category_name = pct.product_category_name
WHERE r.review_score BETWEEN 1 AND 5
GROUP BY category
HAVING COUNT(DISTINCT r.review_id) >= 20
ORDER BY avg_review_score DESC
"""



# =========================================================
# 8. BUSINESS INSIGHTS
# =========================================================

RETENTION_INSIGHT_QUERY = """
SELECT
    COUNT(*) AS unique_customers,
    SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END)
        AS one_time_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
        AS repeat_customers
FROM (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
) AS customer_orders
"""

DELIVERY_INSIGHT_QUERY = """
SELECT
    COUNT(*) AS delivered_orders,
    AVG(
        TIMESTAMPDIFF(
            SECOND,
            order_purchase_timestamp,
            order_delivered_customer_date
        ) / 86400.0
    ) AS avg_delivery_days,
    SUM(
        CASE
            WHEN order_delivered_customer_date
                 > order_estimated_delivery_date
            THEN 1 ELSE 0
        END
    ) AS delayed_orders
FROM orders
WHERE order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL
  AND order_delivered_customer_date >= order_purchase_timestamp
"""

SATISFACTION_INSIGHT_QUERY = """
SELECT
    COUNT(*) AS total_reviews,
    AVG(review_score) AS avg_review_score,
    SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)
        AS low_reviews,
    SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)
        AS positive_reviews
FROM order_reviews
WHERE review_score BETWEEN 1 AND 5
"""
