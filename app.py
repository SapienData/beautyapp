import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import plotly.express as px

# ---------------------------
# PAGE CONFIG & STYLING
# ---------------------------
st.set_page_config(page_title="Beauty Business Dashboard", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #fff8f9; }
    h1, h2, h3 { color: #d63384; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #d63384; }
</style>
""", unsafe_allow_html=True)


# HELPERS

def generate_seasonal_multiplier(date):
    day_of_year = date.timetuple().tm_yday
    return 1 + 0.25 * np.sin(2 * np.pi * (day_of_year / 365) - np.pi / 2)  # Peak in spring/summer

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


# MOCK DATA GENERATION INCLUDING CAMPAIGNS

@st.cache_data
def generate_mock_data(start_date, days=90, brands=None):
    if brands is None:
        brands = ["Radiance", "GlowUp", "PureBeauty"]

    categories = {
        "Skincare": ["Hydrating Serum", "SPF50 Sunscreen", "Vitamin C Cream", "Gentle Cleanser"],
        "Makeup": ["Matte Lipstick", "Glow Foundation", "Brow Kit", "Volumizing Mascara"],
        "Haircare": ["Argan Shampoo", "Keratin Conditioner", "Repair Mask", "Curl Cream"],
        "Fragrance": ["Citrus Mist", "Noir Eau de Parfum", "Floral Bloom"],
        "Body": ["Shea Body Butter", "Exfoliating Scrub", "Aloe Body Gel"]
    }

    channels = ["Online", "In-store", "Wholesale"]
    marketing_channels = ["Organic", "Paid", "Social", "Email"]
    social_platforms = ["Instagram", "Facebook", "TikTok", "YouTube"]
    offers = ["None", "10% Off", "Buy 1 Get 1", "Free Gift"]
    campaigns = ["Summer Glow", "Holiday Sparkle", "Winter Warmth", "Spring Fresh", "Loyalty Boost"]

    dates = pd.date_range(start=start_date, periods=days).tolist()

    sales_records = []
    marketing_records = []
    social_records = []
    reviews_records = []

    for brand in brands:
        followers = {p: random.randint(5000, 15000) for p in social_platforms}

        for date in dates:
            seasonal_mult = generate_seasonal_multiplier(date)
            weekday_factor = 1.1 if date.weekday() in [4,5] else 0.9
            daily_orders = int(clamp(np.random.normal(80 * seasonal_mult * weekday_factor, 15), 40, 150))

            # Assign campaign per day randomly (simulate active campaigns)
            active_campaign = random.choice(campaigns)

            for _ in range(daily_orders):
                cat_weights = {
                    "Radiance": [0.4, 0.3, 0.15, 0.1, 0.05],
                    "GlowUp": [0.3, 0.4, 0.1, 0.1, 0.1],
                    "PureBeauty": [0.25, 0.25, 0.3, 0.1, 0.1]
                }
                cats = list(categories.keys())
                cat = random.choices(cats, weights=cat_weights[brand])[0]
                prod = random.choice(categories[cat])
                channel = random.choices(channels, weights=[0.6, 0.3, 0.1])[0]
                offer = random.choices(offers, weights=[0.7, 0.15, 0.1, 0.05])[0]

                base_price = {
                    "Skincare": 45,
                    "Makeup": 35,
                    "Haircare": 30,
                    "Fragrance": 75,
                    "Body": 25
                }[cat]
                price = round(np.random.normal(base_price, base_price * 0.15), 2)
                price = clamp(price, base_price * 0.6, base_price * 1.5)

                qty = max(1, int(np.random.exponential(1.5)))

                revenue = round(price * qty, 2)
                sales_records.append({
                    "Brand": brand,
                    "Date": date,
                    "Category": cat,
                    "Product": prod,
                    "Channel": channel,
                    "Offer": offer,
                    "Campaign": active_campaign,
                    "Qty": qty,
                    "UnitPrice": price,
                    "Revenue": revenue
                })

            # Marketing with campaign attribution
            for mkt_channel in marketing_channels:
                base_traffic = {
                    "Organic": 1200,
                    "Paid": 800,
                    "Social": 600,
                    "Email": 400
                }[mkt_channel]
                traffic = int(clamp(np.random.normal(base_traffic * seasonal_mult, base_traffic * 0.1), 100, 5000))
                ctr = round(np.random.uniform(0.3, 4.5), 2)
                cpc = round(np.random.uniform(0.3, 2.0), 2) if mkt_channel == "Paid" else None

                marketing_records.append({
                    "Brand": brand,
                    "Date": date,
                    "Channel": mkt_channel,
                    "Campaign": active_campaign,
                    "Traffic": traffic,
                    "CTR": ctr,
                    "CPC": cpc,
                })

            # Social Media
            for platform in social_platforms:
                followers[platform] = int(followers[platform] * np.random.uniform(1.0005, 1.003))
                engagement_rate = round(np.random.uniform(0.5, 8.5), 2)

                social_records.append({
                    "Brand": brand,
                    "Date": date,
                    "Platform": platform,
                    "EngagementRate": engagement_rate,
                    "Followers": followers[platform]
                })

        # Reviews
        sentiments = ["Positive", "Neutral", "Negative"]
        sentiment_weights = [0.7, 0.2, 0.1]
        review_dates = random.choices(dates, k=120)
        for review_date in review_dates:
            sentiment = random.choices(sentiments, weights=sentiment_weights)[0]
            rating_map = {"Positive": random.randint(4,5), "Neutral": 3, "Negative": random.randint(1,2)}
            rating = rating_map[sentiment]

            reviews_records.append({
                "Brand": brand,
                "Date": review_date,
                "Sentiment": sentiment,
                "Rating": rating
            })

    sales_df = pd.DataFrame(sales_records)
    marketing_df = pd.DataFrame(marketing_records)
    social_df = pd.DataFrame(social_records)
    reviews_df = pd.DataFrame(reviews_records)

    for df in [sales_df, marketing_df, social_df, reviews_df]:
        df["Date"] = pd.to_datetime(df["Date"])

    return sales_df, marketing_df, social_df, reviews_df, campaigns

# ---------------------------
# SIDEBAR FILTERS
# ---------------------------
brands_available = ["Radiance", "GlowUp", "PureBeauty"]
default_brands = brands_available.copy()

st.sidebar.header("Filters")
selected_brands = st.sidebar.multiselect("Select Brands", options=brands_available, default=default_brands)

today = datetime.date.today()
start_date = today - datetime.timedelta(days=90)
date_range = st.sidebar.date_input("Select Date Range", [start_date, today], min_value=start_date, max_value=today)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_filter, end_filter = date_range[0], date_range[1]
else:
    start_filter, end_filter = start_date, today

# Load data with campaigns
sales_df, marketing_df, social_df, reviews_df, campaigns = generate_mock_data(start_date, days=(today - start_date).days + 1, brands=brands_available)

# Campaign filter (sidebar)
selected_campaigns = st.sidebar.multiselect("Select Campaigns", options=campaigns, default=campaigns)

# ---------------------------
# FILTER DATA
# ---------------------------
sales_df = sales_df[
    (sales_df["Brand"].isin(selected_brands)) &
    (sales_df["Campaign"].isin(selected_campaigns)) &
    (sales_df["Date"].dt.date >= start_filter) &
    (sales_df["Date"].dt.date <= end_filter)
]

marketing_df = marketing_df[
    (marketing_df["Brand"].isin(selected_brands)) &
    (marketing_df["Campaign"].isin(selected_campaigns)) &
    (marketing_df["Date"].dt.date >= start_filter) &
    (marketing_df["Date"].dt.date <= end_filter)
]

social_df = social_df[
    (social_df["Brand"].isin(selected_brands)) &
    (social_df["Date"].dt.date >= start_filter) &
    (social_df["Date"].dt.date <= end_filter)
]

reviews_df = reviews_df[
    (reviews_df["Brand"].isin(selected_brands)) &
    (reviews_df["Date"].dt.date >= start_filter) &
    (reviews_df["Date"].dt.date <= end_filter)
]

# ---------------------------
# DASHBOARD
# ---------------------------
st.title("Beauty Business Dashboard")
st.markdown("### Comprehensive marketing, sales & customer insights across your brands and campaigns")

# EXECUTIVE SUMMARY
st.subheader("Executive Summary")
total_revenue = sales_df["Revenue"].sum()
total_orders = sales_df["Qty"].sum()
avg_order_value = total_revenue / total_orders if total_orders else 0
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Units Sold", f"{total_orders:,}")
col3.metric("Average Order Value", f"${avg_order_value:.2f}")

cac = round(np.random.uniform(25, 40), 2)
clv = round(np.random.uniform(200, 350), 2)
mkt_roi = round(np.random.uniform(2.5, 4.0), 2)
col4, col5, col6 = st.columns(3)
col4.metric("Customer Acquisition Cost (CAC)", f"${cac:.2f}")
col5.metric("Customer Lifetime Value (CLV)", f"${clv}")
col6.metric("Marketing ROI (x)", f"{mkt_roi}")

# SALES & REVENUE
st.subheader("Sales & Revenue")
cat_brand_rev = sales_df.groupby(["Brand", "Category"])["Revenue"].sum().reset_index()
fig_cat_brand = px.bar(
    cat_brand_rev, x="Category", y="Revenue", color="Brand",
    title="Revenue by Category & Brand", barmode="group",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_cat_brand, use_container_width=True)

st.markdown("### Top Products by Revenue")
top_products = sales_df.groupby(["Brand", "Product"])["Revenue"].sum().reset_index()
top_products = top_products.sort_values("Revenue", ascending=False).groupby("Brand").head(10)
top_products = top_products[top_products["Brand"].isin(selected_brands)]
fig_top_prod = px.bar(
    top_products, x="Product", y="Revenue", color="Brand",
    title="Top 10 Products by Revenue per Brand",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_top_prod, use_container_width=True)

ch_rev = sales_df.groupby(["Brand", "Channel"])["Revenue"].sum().reset_index()
fig_ch = px.bar(
    ch_rev, x="Channel", y="Revenue", color="Brand",
    title="Revenue by Sales Channel & Brand", barmode="group",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_ch, use_container_width=True)

seasonal_rev = sales_df.groupby("Date")["Revenue"].sum().reset_index()
fig_seasonal = px.line(
    seasonal_rev, x="Date", y="Revenue",
    title="Seasonal Revenue Trends Over Time",
    color_discrete_sequence=["#d63384"])
st.plotly_chart(fig_seasonal, use_container_width=True)

offer_rev = sales_df.groupby("Offer")["Revenue"].sum().reset_index()
fig_offer = px.pie(
    offer_rev, values="Revenue", names="Offer",
    title="Revenue Distribution by Promotion Type",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_offer, use_container_width=True)

# MARKETING PERFORMANCE
st.subheader("Marketing Performance")
fig_marketing_traffic = px.line(
    marketing_df, x="Date", y="Traffic", color="Channel",
    line_dash="Brand", title="Website Traffic by Channel & Brand",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_marketing_traffic, use_container_width=True)

paid_ads = marketing_df[marketing_df["Channel"] == "Paid"]
fig_ctr = px.line(
    paid_ads, x="Date", y="CTR", color="Brand",
    title="Paid Ad CTR Over Time",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_ctr, use_container_width=True)

fig_cpc = px.line(
    paid_ads.dropna(subset=["CPC"]), x="Date", y="CPC", color="Brand",
    title="Paid Ad CPC Over Time",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_cpc, use_container_width=True)

# Campaign Traffic Summary
campaign_traffic = marketing_df.groupby(["Campaign", "Channel"])["Traffic"].sum().reset_index()
fig_campaign_traffic = px.bar(
    campaign_traffic, x="Campaign", y="Traffic", color="Channel",
    title="Total Traffic by Campaign & Channel",
    barmode="stack",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_campaign_traffic, use_container_width=True)

# Email Campaign Performance (Open Rate & CTR simulated)
email_campaigns = marketing_df[marketing_df["Channel"] == "Email"]
email_campaign_summary = email_campaigns.groupby("Campaign").agg({
    "Traffic": "sum",
    "CTR": "mean"
}).reset_index()
email_campaign_summary["Open Rate (%)"] = email_campaign_summary["CTR"] * random.uniform(20,40) / 100  # simulated
email_campaign_summary["Conversion Rate (%)"] = email_campaign_summary["CTR"] * random.uniform(5,15) / 100  # simulated

fig_email = px.bar(
    email_campaign_summary, x="Campaign",
    y=["Open Rate (%)", "Conversion Rate (%)"],
    title="Email Campaign Performance",
    barmode="group",
    color_discrete_sequence=["#d63384", "#6c757d"])
st.plotly_chart(fig_email, use_container_width=True)

# CUSTOMER INSIGHTS
st.subheader("Customer Insights")

loyalty_rate = round(np.random.uniform(40, 70), 2)
repeat_purchase_rate = round(np.random.uniform(30, 60), 2)

col1, col2 = st.columns(2)
col1.metric("Loyalty Program Participation", f"{loyalty_rate}%")
col2.metric("Repeat Purchase Rate", f"{repeat_purchase_rate}%")

# New vs Returning Customers (simulated)
sales_df["IsNewCustomer"] = np.random.choice([True, False], size=len(sales_df), p=[0.35, 0.65])
new_customers = sales_df[sales_df["IsNewCustomer"]].groupby("Date").size().cumsum()
returning_customers = sales_df[~sales_df["IsNewCustomer"]].groupby("Date").size().cumsum()

cust_trends = pd.DataFrame({
    "Date": new_customers.index,
    "New Customers": new_customers.values,
    "Returning Customers": returning_customers.reindex(new_customers.index, fill_value=0).values
}).melt(id_vars="Date", var_name="Customer Type", value_name="Count")

fig_cust = px.line(
    cust_trends, x="Date", y="Count", color="Customer Type",
    title="New vs Returning Customers Over Time",
    color_discrete_map={"New Customers": "#d63384", "Returning Customers": "#6c757d"})
st.plotly_chart(fig_cust, use_container_width=True)

# BRAND AWARENESS & SENTIMENT
st.subheader("Brand Awareness & Sentiment")

sentiment_counts = reviews_df.groupby(["Brand", "Sentiment"]).size().reset_index(name="Count")
fig_sentiment = px.bar(
    sentiment_counts, x="Brand", y="Count", color="Sentiment",
    title="Customer Review Sentiment by Brand",
    color_discrete_map={"Positive": "#d63384", "Neutral": "#ffccd5", "Negative": "#6c757d"},
    barmode="stack")
st.plotly_chart(fig_sentiment, use_container_width=True)

# SOCIAL MEDIA PERFORMANCE
st.subheader("Social Media Engagement")

social_summary = social_df.groupby(["Brand", "Platform"]).agg({
    "EngagementRate": "mean",
    "Followers": "max"
}).reset_index()

fig_social = px.scatter(
    social_summary, x="Followers", y="EngagementRate",
    color="Brand", symbol="Platform", size="EngagementRate",
    title="Social Media Followers & Engagement Rate by Platform & Brand",
    color_discrete_sequence=px.colors.sequential.RdPu)
st.plotly_chart(fig_social, use_container_width=True)