import streamlit as st
import pandas as pd
import plotly.express as px

# page
st.set_page_config(page_title="Marketing Dashboard", layout="wide")

# app styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0A192F;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# styling function for plots
def style_plot(fig):
    fig.update_layout(
        plot_bgcolor="#0A192F",
        paper_bgcolor="#0A192F",
        font_color="white",
        xaxis=dict(color="white", showgrid=False),
        yaxis=dict(color="white", showgrid=False)
    )
    return fig

# func to styling kpis
def display_kpi(kpi_items):
    cols = st.columns(len(kpi_items))
    for col, (label, value) in zip(cols, kpi_items):
        with col:
            st.markdown(f"""
                <div style='background-color: #112B44; padding: 20px; border-radius: 10px; text-align: center; color: white; font-size: 20px;'>
                    <strong>{label}</strong><br>
                    <span style='font-size: 28px;'>{value}</span>
                </div>
            """, unsafe_allow_html=True)

# --- data loading ---
def load_data(file):
    return pd.read_csv(file)

# load default or uploaded data
st.sidebar.title("📂 Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    df = load_data("clean_data.csv")

# --- columns lists ---
product_cols = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
purchase_channels = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
cmp_cols = ['AcceptedCmp1','AcceptedCmp2','AcceptedCmp3','AcceptedCmp4','AcceptedCmp5']

# --- feature engineering ---
df["Join_Year"] = pd.to_datetime(df["Dt_Customer"]).dt.year
df["Join_Month"] = pd.to_datetime(df["Dt_Customer"]).dt.month
df["Total_Spend"] = df[product_cols].sum(axis=1)
df["Campaign_Accepted_Count"] = df[cmp_cols].sum(axis=1)

# --- tabs layout ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dataset", "Customer", "Spending", "Campaigns", "Chatbot"])

# 📁 Dataset Tab
with tab1:
    st.title("📁 Dataset Preview")
    column = st.selectbox("Select Column", df.columns)
    value = st.text_input("Search")
    if value:
        result = df[df[column].astype(str).str.contains(value)]
        st.write(f"Found {result.shape[0]} rows")
        st.dataframe(result)
    else:
        st.dataframe(df.head())

#Customer Tab
with tab2:
    st.header("Customer Overview")
    min_age, max_age = int(df["age"].min()), int(df["age"].max())
    age_range = st.slider("Select Age Range", min_value=min_age, max_value=max_age, value=(min_age, max_age))
    filtered_df = df[(df["age"] >= age_range[0]) & (df["age"] <= age_range[1])]
    display_kpi([
        ("Total Customers", len(filtered_df)),
        ("Average Income", f"${int(filtered_df['Income'].mean()):,}"),
        ("Campaign Response Rate", f"{round((filtered_df['Campaign_Accepted_Count'] > 0).mean() * 100, 2)}%")
    ])

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = px.histogram(filtered_df, x="Income", nbins=30, color_discrete_sequence=["#00B4D8"])
        st.subheader("💰 Income Distribution")
        st.plotly_chart(style_plot(fig), use_container_width=True, key="income_dist")

    with col2:
        fig = px.box(filtered_df, x="age", y="Total_Spend", points="all", color_discrete_sequence=["#00B4D8"])
        st.subheader("🎯 Age vs Total Spend")
        st.plotly_chart(style_plot(fig), use_container_width=True, key="age_vs_spend")

    with col3:
        st.subheader("📈 Income vs Campaign Response")
        fig = px.box(filtered_df,
                     x="Campaign_Accepted_Count",
                     y="Income",
                     points="all",
                     color_discrete_sequence=["#00B4D8"])
        st.plotly_chart(style_plot(fig), use_container_width=True, key="income_vs_campaign")

#Spending Tab
with tab3:
    st.header("Spending Overview")
    income_range = st.slider("Filter by Income", int(df["Income"].min()), int(df["Income"].max()), (20000, 60000))
    selected_product = st.selectbox("Select Product Type", product_cols)
    spend_df = df[(df["Income"] >= income_range[0]) & (df["Income"] <= income_range[1])].copy()
    spend_df["Selected_Product_Spend"] = spend_df[selected_product]

    display_kpi([
        ("Total Spend", f"${int(spend_df['Total_Spend'].sum()):,}"),
        ("Avg Spend per Customer", f"${int(spend_df['Total_Spend'].mean()):,}"),
    ])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛒 Spend per Product Category")
        totals = spend_df[product_cols].sum().sort_values(ascending=False)
        fig = px.bar(x=totals.index, y=totals.values, color_discrete_sequence=["#00B4D8"])
        st.plotly_chart(style_plot(fig), use_container_width=True, key="spend_product")

    with col2:
        st.subheader("📈 Spend Over Time")
        time_df = spend_df.groupby(["Join_Year", "Join_Month"])["Total_Spend"].sum().reset_index()
        time_df["Join_Date"] = pd.to_datetime(time_df["Join_Year"].astype(str) + "-" + time_df["Join_Month"].astype(str))
        fig = px.line(time_df, x="Join_Date", y="Total_Spend", markers=True)
        st.plotly_chart(style_plot(fig), use_container_width=True, key="spend_over_time")

    st.subheader("Spending by Marital Status")
    fig = px.box(spend_df, x="Marital_Status", y="Total_Spend", color="Marital_Status",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(style_plot(fig), use_container_width=True, key="spend_marital_status")

#Campaigns Tab
with tab4:
    display_kpi([
        ("Accepted Campaigns", f"{int(filtered_df[cmp_cols].sum().sum())}"),
        ("Responded Customers", f"{filtered_df[filtered_df['Campaign_Accepted_Count'] > 0].shape[0]}"),
    ])

    st.subheader("📊 Campaign Acceptance Distribution")
    totals = df[cmp_cols].sum()
    fig = px.bar(x=totals.index, y=totals.values, color_discrete_sequence=["#00B4D8"])
    st.plotly_chart(style_plot(fig), use_container_width=True, key="campaign_acceptance")

    st.subheader("🛍️ Top Purchase Channels")
    channel_totals = filtered_df[purchase_channels].sum().sort_values(ascending=False)
    fig = px.bar(x=channel_totals.index, y=channel_totals.values, text=channel_totals.values,
                 labels={"x": "Channel", "y": "Total Purchases"}, color_discrete_sequence=["#00B4D8"])
    st.plotly_chart(style_plot(fig), use_container_width=True, key="top_channels")

    st.subheader("📦 Channel Purchases vs Campaign Response")
    filtered_df["Total_Channel_Purchases"] = filtered_df[purchase_channels].sum(axis=1)
    filtered_df["Responded"] = filtered_df["Campaign_Accepted_Count"].apply(lambda x: "Yes" if x > 0 else "No")
    fig = px.box(filtered_df, x="Responded", y="Total_Channel_Purchases", color="Responded",
                 color_discrete_sequence=["#00B4D8", "#90E0EF"])
    st.plotly_chart(style_plot(fig), use_container_width=True, key="channel_vs_response")

#Chatbot Tab
with tab5:
    st.header("🤖 Chatbot")
    st.markdown("Ask a question about the dataset:")

    question = st.selectbox("Choose a question:", [
        "What is the most common age among customers?",
        "How many total customers are in the dataset?",
        "What is the average customer income?",
        "What is the total and average spend per customer?",
        "Which product category has the highest average spend?",
        "How much is spent on each product type?",
        "Which purchase channel is most preferred?",
        "How many purchases occurred through each channel?",
        "What is the average number of website visits per month?",
        "What is the overall response rate to campaigns?",
        "How many customers accepted more than one campaign?",
        "How many responses were there for each campaign?",
        "How many customers are old vs new based on 1000 days?"
    ])

    if st.button("💬 Get Answer"):
        if question == "What is the most common age among customers?":
            st.success(f"The most common age is: {df['age'].mode()[0]}")
        elif question == "How many total customers are in the dataset?":
            st.success(f"Total number of customers: {df.shape[0]}")
        elif question == "What is the average customer income?":
            st.success(f"The average income is: ${int(df['Income'].mean()):,}")
        elif question == "What is the total and average spend per customer?":
            st.success(f"Total Spend: ${int(df['Total_Spend'].sum()):,}, Average Spend per Customer: ${int(df['Total_Spend'].mean()):,}")
        elif question == "Which product category has the highest average spend?":
            top_product = df[product_cols].mean().idxmax()
            st.success(f"The product category with the highest average spend is: {top_product}")
        elif question == "How much is spent on each product type?":
            st.write(df[product_cols].sum().sort_values(ascending=False))
        elif question == "Which purchase channel is most preferred?":
            top_channel = df[purchase_channels].mean().idxmax()
            st.success(f"The most preferred purchase channel is: {top_channel}")
        elif question == "How many purchases occurred through each channel?":
            st.write(df[purchase_channels].sum().sort_values(ascending=False))
        elif question == "What is the average number of website visits per month?":
            st.success(f"Average Website Visits per Month: {df['NumWebVisitsMonth'].mean():.2f}")
        elif question == "What is the overall response rate to campaigns?":
            st.success(f"Response Rate: {df['Response'].mean()*100:.2f}%")
        elif question == "How many customers accepted more than one campaign?":
            st.success(f"Customers who accepted more than one campaign: {(df['Campaign_Accepted_Count'] > 1).sum()}")
        elif question == "How many responses were there for each campaign?":
            st.write(df[cmp_cols].sum().sort_values(ascending=False))
        elif question == "How many customers are old vs new based on 1000 days?":
            df['Customer_Since_Days'] = (pd.to_datetime("today") - pd.to_datetime(df["Dt_Customer"])).dt.days
            old_customers = (df['Customer_Since_Days'] > 1000).sum()
            new_customers = (df['Customer_Since_Days'] <= 1000).sum()
            st.success(f"Old Customers (>1000 days): {old_customers}, New Customers (<=1000 days): {new_customers}")
