import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# -------------------------------------------------
# PAGE SETTINGS
# -------------------------------------------------

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="centered"
)


# -------------------------------------------------
# CUSTOM MOBILE-FRIENDLY DESIGN
# -------------------------------------------------

st.markdown("""
<style>

.block-container {
    max-width: 600px;
    padding-top: 25px;
    padding-bottom: 30px;
}

/* Main title */
.main-title {
    text-align: center;
    font-size: 26px;
    font-weight: bold;
    line-height: 1.4;
    padding: 10px 0;
    margin: 0;
    white-space: nowrap;
    overflow: visible;
}

/* Month text */
.month-text {
    text-align: center;
    font-size: 17px;
    opacity: 0.7;
    margin-bottom: 25px;
}

/* Expense cards */
.expense-card {
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
    border: 1px solid #dddddd;
}

/* Amount */
.amount-text {
    font-size: 24px;
    font-weight: bold;
}

/* Total card */
.total-card {
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #dddddd;
    margin-top: 15px;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------

conn = sqlite3.connect(
    "expenses.db",
    check_same_thread=False
)

cursor = conn.cursor()


# -------------------------------------------------
# CREATE DATABASE TABLE
# -------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    month_key TEXT,
    category TEXT,
    amount REAL

)
""")

conn.commit()

# -------------------------------------------------
# ADD month_key COLUMN TO OLD DATABASE
# -------------------------------------------------

cursor.execute("PRAGMA table_info(expenses)")
columns = [column[1] for column in cursor.fetchall()]

if "month_key" not in columns:

    cursor.execute(
        "ALTER TABLE expenses ADD COLUMN month_key TEXT"
    )

    conn.commit()


# -------------------------------------------------
# FIX OLD SAVED DATA
# -------------------------------------------------

cursor.execute("""
    SELECT id, month
    FROM expenses
    WHERE month_key IS NULL
""")

old_rows = cursor.fetchall()


for row_id, month_name in old_rows:

    try:

        converted_date = datetime.strptime(
            month_name,
            "%B %Y"
        )

        month_key = converted_date.strftime(
            "%Y-%m"
        )

        cursor.execute("""
            UPDATE expenses
            SET month_key = ?
            WHERE id = ?
        """, (
            month_key,
            row_id
        ))

    except Exception:
        pass


conn.commit()


# -------------------------------------------------
# KEEP ONLY LAST 12 MONTHS
# -------------------------------------------------

today = datetime.now()

total_months = (
    today.year * 12 +
    today.month
)

cutoff_total_months = (
    total_months - 11
)

cutoff_year = (
    cutoff_total_months - 1
) // 12

cutoff_month = (
    cutoff_total_months - 1
) % 12 + 1

cutoff_month_key = (
    f"{cutoff_year:04d}-{cutoff_month:02d}"
)

cursor.execute(
    """
    DELETE FROM expenses
    WHERE month_key < ?
    """,
    (
        cutoff_month_key,
    )
)

conn.commit()

# -------------------------------------------------
# ADD month_key COLUMN TO OLD DATABASE
# -------------------------------------------------

cursor.execute("PRAGMA table_info(expenses)")
columns = [column[1] for column in cursor.fetchall()]

if "month_key" not in columns:

    cursor.execute(
        "ALTER TABLE expenses ADD COLUMN month_key TEXT"
    )

    conn.commit()


# -------------------------------------------------
# FIX OLD SAVED DATA
# -------------------------------------------------

cursor.execute("""
    SELECT id, month
    FROM expenses
    WHERE month_key IS NULL
""")

old_rows = cursor.fetchall()


for row_id, month_name in old_rows:

    try:
        converted_date = datetime.strptime(
            month_name,
            "%B %Y"
        )

        month_key = converted_date.strftime("%Y-%m")

        cursor.execute("""
            UPDATE expenses
            SET month_key = ?
            WHERE id = ?
        """, (
            month_key,
            row_id
        ))

    except:
        pass


conn.commit()


# -------------------------------------------------
# CURRENT MONTH
# -------------------------------------------------

# -------------------------------------------------
# CURRENT MONTH
# -------------------------------------------------

current_month = datetime.now().strftime("%B %Y")

# Hidden format used for correct month sorting
# Example: 2026-09
current_month_key = datetime.now().strftime("%Y-%m")


# -------------------------------------------------
# FIXED CATEGORIES
# -------------------------------------------------

categories = [
    "🍔 Food & Snacks",
    "🚌 Travelling",
    "🛍️ Shopping",
    "🎬 Entertainment",
    "💊 Health & Medicine",
    "📦 Other"
]


# -------------------------------------------------
# APP HEADER
# -------------------------------------------------

st.markdown(
    '<div class="main-title">💰 Expense Tracker</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="month-text">{current_month}</div>',
    unsafe_allow_html=True
)


# -------------------------------------------------
# ADD EXPENSE
# -------------------------------------------------

st.subheader("➕ Add Expense")


category = st.selectbox(
    "Choose Category",
    categories
)


amount = st.number_input(
    "Enter Amount (₹)",
    min_value=0.0,
    step=10.0
)


if st.button(
    "➕ ADD EXPENSE",
    use_container_width=True
):

    if amount > 0:

        cursor.execute(
    """
    INSERT INTO expenses
    (
        month,
        month_key,
        category,
        amount
    )

    VALUES (?, ?, ?, ?)
    """,

    (
        current_month,
        current_month_key,
        category,
        amount
    )
)

        conn.commit()

        st.success("Expense added successfully! 💰")

    else:

        st.warning(
            "Please enter an amount greater than ₹0."
        )


# -------------------------------------------------
# LOAD CURRENT MONTH DATA
# -------------------------------------------------

df = pd.read_sql_query(
    """
    SELECT category,
           SUM(amount) AS total

    FROM expenses

    WHERE month_key = ?

    GROUP BY category
    """,

    conn,

    params=(current_month_key,)
)


# -------------------------------------------------
# CREATE TOTALS FOR ALL CATEGORIES
# -------------------------------------------------

expense_totals = {}

for cat in categories:

    if cat in df["category"].values:

        total = df.loc[
            df["category"] == cat,
            "total"
        ].iloc[0]

        expense_totals[cat] = total

    else:

        expense_totals[cat] = 0


# -------------------------------------------------
# SHOW CURRENT MONTH EXPENSES
# -------------------------------------------------

st.divider()

st.subheader("📊 Your Expenses")


for cat, total in expense_totals.items():

    st.markdown(
        f"""
        <div class="expense-card">

        <div>{cat}</div>

        <div class="amount-text">
        ₹{total:,.0f}
        </div>

        </div>
        """,

        unsafe_allow_html=True
    )


# -------------------------------------------------
# TOTAL SPENT
# -------------------------------------------------

total_spent = sum(
    expense_totals.values()
)


st.divider()


if "show_total" not in st.session_state:

    st.session_state.show_total = False


if st.button(
    "👁️ Show / Hide Total Spent",
    use_container_width=True
):

    st.session_state.show_total = (
        not st.session_state.show_total
    )


if st.session_state.show_total:

    total_display = (
        f"₹{total_spent:,.0f}"
    )

else:

    total_display = (
        "₹ ••••••"
    )


st.markdown(
    f"""
    <div class="total-card">

    <div>💰 TOTAL SPENT</div>

    <div class="amount-text">
    {total_display}
    </div>

    </div>
    """,

    unsafe_allow_html=True
)


# -------------------------------------------------
# PREPARE DATA FOR CHARTS
# -------------------------------------------------

chart_data = pd.DataFrame({

    "Category":
        list(expense_totals.keys()),

    "Amount":
        list(expense_totals.values())

})


# Remove categories with ₹0 from charts
chart_data = chart_data[
    chart_data["Amount"] > 0
]


# -------------------------------------------------
# BEAUTIFUL COMPACT PIE CHART
# -------------------------------------------------

if not chart_data.empty:

    st.subheader("🥧 Spending by Category")

    fig, ax = plt.subplots(figsize=(5, 5))

    wedges, texts, autotexts = ax.pie(
        chart_data["Amount"],
        labels=None,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.75,
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 2
        }
    )

    # Make percentage text readable
    for text in autotexts:
        text.set_fontsize(11)
        text.set_fontweight("bold")

    ax.legend(
        wedges,
        chart_data["Category"],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=False,
        fontsize=9
    )

    ax.set_aspect("equal")

    st.pyplot(
        fig,
        use_container_width=True
    )

    plt.close(fig)


# -------------------------------------------------
# BEAUTIFUL COMPACT BAR CHART
# -------------------------------------------------

if not chart_data.empty:

    st.subheader("📊 Category Comparison")

    fig2, ax2 = plt.subplots(figsize=(6, 4))

    colors = [
        "#FF9F43",  # Food & Snacks
        "#4D96FF",  # Travelling
        "#9B59B6",  # Shopping
        "#FF6B6B",  # Entertainment
        "#2ECC71",  # Health & Medicine
        "#95A5A6"   # Other
    ]

    bars = ax2.bar(
        chart_data["Category"],
        chart_data["Amount"],
        color=colors[:len(chart_data)]
    )

    ax2.set_ylabel("Amount (₹)")

    # Rotate category names for mobile
    ax2.tick_params(
        axis="x",
        labelrotation=35,
        labelsize=8
    )

    # Show amount above every bar
    for bar in bars:

        height = bar.get_height()

        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"₹{height:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    # Clean unnecessary borders
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()

    st.pyplot(
        fig2,
        use_container_width=True
    )

    plt.close(fig2)

 
 

# -------------------------------------------------
# PREVIOUS MONTHS
# -------------------------------------------------

st.divider()

st.subheader("📜 Your Expenses — Previous Months")


previous_months = pd.read_sql_query(
    """
    SELECT
        month,
        month_key,
        SUM(amount) AS total

    FROM expenses

    WHERE month_key != ?

    GROUP BY
        month,
        month_key

    ORDER BY month_key DESC
    """,

    conn,

    params=(current_month_key,)
)


if previous_months.empty:

    st.info(
        "No previous month expenses yet."
    )

else:

    for _, row in previous_months.iterrows():

        st.markdown(
            f"""
            <div class="expense-card">

                <div style="
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 5px;
                ">
                    📅 {row["month"]}
                </div>

                <div style="
                    font-size: 22px;
                    font-weight: bold;
                ">
                    Total: ₹{row["total"]:,.0f}
                </div>

            </div>
            """,

            unsafe_allow_html=True
        )




        



# -------------------------------------------------
# DELETE DATA OLDER THAN 12 MONTHS
# -------------------------------------------------

# We will improve this cleanup system
# in the next step.
# It is intentionally not deleting data yet
# because month names alone are not ideal
# for accurate 12-month calculations.