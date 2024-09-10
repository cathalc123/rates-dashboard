import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from scipy.stats import zscore
from tvDatafeed import TvDatafeedLive

tvl = TvDatafeedLive()

st.set_page_config("Macro Dashboard", layout = "wide")
st.title("Rates Dashboard")

symbols_tvc = ['US10Y', 'US30Y', 'US02Y', 'US05Y']
symbols_cme = ['SR3Z2024', 'SR3Z2025', 'SR3H2025', 'SR3M2025', "SR3U2025", "SR3Z2025"]
symbols_eurex = ["ER3Z2024", "ER3Z2025", "ER3H2025", "ER3M2025", "ER3U2025"]
rerun = st.button("Update Data")

@st.cache_data
def load_data():
    df_list = []

    # Fetch historical data
    for symbol in symbols_tvc:
        data = tvl.get_hist(symbol=symbol, exchange='TVC', n_bars=370)
        data['symbol'] = symbol
        df_list.append(data)

    for symbol in symbols_cme:
        data = tvl.get_hist(symbol=symbol, exchange='CME', n_bars=370)
        data['symbol'] = symbol
        df_list.append(data)

    for symbol in symbols_eurex:
        data = tvl.get_hist(symbol=symbol, exchange='ICEEUR', n_bars=370)
        data['symbol'] = symbol
        df_list.append(data)

    # Combine all dataframes
    combined_df = pd.concat(df_list)
    combined_df = combined_df.dropna()
    return combined_df


combined_df = load_data()



if rerun:
    load_data.clear()
    combined_df = load_data()


# Extract data by symbol
us10y_data = combined_df[combined_df['symbol'] == 'US10Y']
us30y_data = combined_df[combined_df['symbol'] == 'US30Y']
us02y_data = combined_df[combined_df['symbol'] == 'US02Y']
us05y_data = combined_df[combined_df['symbol'] == 'US05Y']
z4_data = combined_df[combined_df['symbol'] == 'SR3Z2024']
z5_data = combined_df[combined_df['symbol'] == 'SR3Z2025']
h5_data = combined_df[combined_df["symbol"] == "SR3H2025"]
m5_data = combined_df[combined_df["symbol"] == "SR3M2025"]
u5_data = combined_df[combined_df["symbol"] == "SR3U2025"]
z4_estr_data = combined_df[combined_df["symbol"] == "ER3Z2024"]
z5_estr_data = combined_df[combined_df["symbol"] == "ER3Z2025"]
h5_estr_data = combined_df[combined_df["symbol"] == "ER3H2025"]
m5_estr_data = combined_df[combined_df["symbol"] == "ER3M2025"]
u5_estr_data = combined_df[combined_df["symbol"] == "ER3U2025"]

spreads_df = pd.DataFrame(index=combined_df.index)

spreads_df['usd2s10s'] = us10y_data['close'] - us02y_data['close']
spreads_df['usd2s30s'] = us30y_data['close'] - us02y_data['close']
spreads_df['usd5s30s'] = us30y_data['close'] - us05y_data['close']
spreads_df['usd2s10s30s'] = us10y_data['close'] * 2 - (us02y_data['close'] + us30y_data['close'])
spreads_df['usd5s10s30s'] = us10y_data['close'] * 2 - (us05y_data['close'] + us30y_data['close'])
spreads_df['usd2s5s10s'] = us05y_data['close'] * 2 - (us02y_data['close'] + us10y_data['close'])

spreads_df_usd_stir = pd.DataFrame(index = z4_data.index)

spreads_df_usd_stir['z4h5'] = z4_data['close'] - h5_data['close']
spreads_df_usd_stir['z4m5'] = z4_data['close'] - m5_data['close']
spreads_df_usd_stir["z4u5"] = z4_data["close"] - u5_data["close"]
spreads_df_usd_stir["z4"] = z4_data["close"]
spreads_df_usd_stir["u5"] = u5_data["close"]
spreads_df_usd_stir["h5"] = h5_data['close']
spreads_df_usd_stir["m5"] = m5_data["close"]

spreads_df_eur_stir = pd.DataFrame(index = z4_estr_data.index)

spreads_df_eur_stir['z4h5'] = z4_estr_data['close'] - h5_estr_data['close']
spreads_df_eur_stir['z4m5'] = z4_estr_data['close'] - m5_estr_data['close']
spreads_df_eur_stir["z4u5"] = z4_estr_data["close"] - u5_estr_data["close"]
spreads_df_eur_stir["z4"] = z4_estr_data["close"]
spreads_df_eur_stir["u5"] = u5_estr_data["close"]
spreads_df_eur_stir["h5"] = h5_estr_data['close']
spreads_df_eur_stir["m5"] = m5_estr_data["close"]


with st.sidebar:
    pages = st.radio("Page", ["USD Rates", "EUR Rates", "RV Heatmap"])
    time_range = st.selectbox(
        "Select the time range for regression:",
        ("1 Month", "6 Months", "1 Year", "5 Years", "All Years")
    )

if pages == "USD Rates":
    tab1, tab2 = st.tabs(["STIR", "2y+"])
    with st.sidebar:
        display_zscores = st.checkbox("Display as Z-Scores")
        difference_data = st.checkbox("Difference Data")


    # Filter the spreads data based on time range
    today = spreads_df.index[-1]  # This should now be a datetime object
    if time_range == "1 Month":
        start_date = today - pd.DateOffset(months=1)
    elif time_range == "6 Months":
        start_date = today - pd.DateOffset(months=6)
    elif time_range == "1 Year":
        start_date = today - pd.DateOffset(years=1)
    elif time_range == "5 Years":
        start_date = today - pd.DateOffset(years=5)
    else:
        start_date = spreads_df.index[0]

    filtered_spreads = spreads_df[spreads_df.index >= start_date]

    # Create separate variables for transformed data and regression data
    filtered_spreads_transformed = filtered_spreads.copy()  # This will be used for time series plots
    filtered_spreads_regression = filtered_spreads.copy()   # This will be used for regression plots (unmodified)

    # Apply differencing only to the transformed data
    if difference_data:
        filtered_spreads_transformed = filtered_spreads_transformed.diff().dropna()

    # Apply z-scores only to the transformed data (time series)
    if display_zscores:
        for col in filtered_spreads_transformed.columns:
            filtered_spreads_transformed[f"{col}_zscore"] = zscore(filtered_spreads_transformed[col])

    

with tab2:
    today = spreads_df.index[-1]  # This should now be a datetime object
    if time_range == "1 Month":
        start_date = today - pd.DateOffset(months=1)
    elif time_range == "6 Months":
        start_date = today - pd.DateOffset(months=6)
    elif time_range == "1 Year":
        start_date = today - pd.DateOffset(years=1)
    elif time_range == "5 Years":
        start_date = today - pd.DateOffset(years=5)
    else:
        start_date = spreads_df.index[0]

    filtered_spreads = spreads_df[spreads_df.index >= start_date]

    # Create separate variables for transformed data and regression data
    filtered_spreads_transformed = filtered_spreads.copy()  # For time series plots
    filtered_spreads_regression = filtered_spreads.copy()   # For regression plots (unmodified)

    # Apply differencing only to the transformed data
    if difference_data:
        filtered_spreads_transformed = filtered_spreads_transformed.diff().dropna()

    # Apply z-scores only to the transformed data (time series)
    if display_zscores:
        for col in filtered_spreads_transformed.columns:
            filtered_spreads_transformed[f"{col}_zscore"] = zscore(filtered_spreads_transformed[col])

    # Categorize data based on specific dates
    filtered_spreads_regression['highlight'] = 'Other'
    filtered_spreads_regression.loc[filtered_spreads_regression.index == today, 'highlight'] = 'Today'
    filtered_spreads_regression.loc[filtered_spreads_regression.index == today - pd.Timedelta(weeks=1), 'highlight'] = 'Last Week'
    filtered_spreads_regression.loc[filtered_spreads_regression.index == today - pd.DateOffset(months=1), 'highlight'] = 'One Month Ago'

    # Set point sizes for highlights
    filtered_spreads_regression['size'] = np.where(filtered_spreads_regression['highlight'] == 'Other', 5, 15)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.metric("USD 2s10s", filtered_spreads_transformed["usd2s10s"].iloc[-1].round(2),
                  (filtered_spreads_transformed["usd2s10s"].iloc[-1] - filtered_spreads_transformed["usd2s10s"].iloc[-2]).round(2))
        fig = px.line(filtered_spreads_transformed, y="usd2s10s_zscore" if display_zscores else "usd2s10s",
                      title="USD 2s10s Spread Over Time")
        st.plotly_chart(fig)

        st.metric("USD 5s30s", filtered_spreads_transformed["usd5s30s"].iloc[-1].round(2),
                  (filtered_spreads_transformed["usd5s30s"].iloc[-1] - filtered_spreads_transformed["usd5s30s"].iloc[-2]).round(2))
        fig2 = px.line(filtered_spreads_transformed, y="usd5s30s_zscore" if display_zscores else "usd5s30s",
                       title="USD 5s30s Spread Over Time")
        st.plotly_chart(fig2)

        fig3 = px.line(filtered_spreads_transformed, y="usd2s30s_zscore" if display_zscores else "usd2s30s",
                       title="USD 2s30s Spread Over Time")
        st.plotly_chart(fig3)

    with col2:
        st.metric("USD 2s30s", filtered_spreads_transformed["usd2s30s"].iloc[-1].round(2),
                  (filtered_spreads_transformed["usd2s30s"].iloc[-1] - filtered_spreads_transformed["usd2s30s"].iloc[-2]).round(2))

        # Regression plots (unmodified data)
        fig4 = px.scatter(
            filtered_spreads_regression, x="usd2s10s", y="usd5s30s",
            color='highlight', trendline="ols",
            title="USD 2s10s vs 5s30s"
        )
        st.plotly_chart(fig4)

        fig5 = px.scatter(
            filtered_spreads_regression, x="usd2s10s", y="usd2s30s",
            color='highlight', trendline="ols",
            title="USD 2s10s vs 2s30s"
        )
        st.plotly_chart(fig5)

    # Display metrics and charts for "STIR" tab
    with tab1:
        today = spreads_df_usd_stir.index[-1]  # This should now be a datetime object
        if time_range == "1 Month":
            start_date = today - pd.DateOffset(months=1)
        elif time_range == "6 Months":
            start_date = today - pd.DateOffset(months=6)
        elif time_range == "1 Year":
            start_date = today - pd.DateOffset(years=1)
        elif time_range == "5 Years":
            start_date = today - pd.DateOffset(years=5)
        else:
            start_date = spreads_df_usd_stir.index[0]  # Corrected from `spreads_df.index[0]`

        filtered_spreads = spreads_df_usd_stir[spreads_df_usd_stir.index >= start_date]

        # Create separate variables for transformed data and regression data
        filtered_spreads_transformed = filtered_spreads.copy()  # For time series plots
        filtered_spreads_regression = filtered_spreads.copy()   # For regression plots (unmodified)

        # Apply differencing only to the transformed data
        if difference_data:
            filtered_spreads_transformed = filtered_spreads_transformed.diff().dropna()

        # Apply z-scores only to the transformed data (time series)
        if display_zscores:
            for col in filtered_spreads_transformed.columns:
                filtered_spreads_transformed[f"{col}_zscore"] = zscore(filtered_spreads_transformed[col])

        # Categorize data based on specific dates
        filtered_spreads_regression['highlight'] = 'Other'
        filtered_spreads_regression.loc[filtered_spreads_regression.index == today, 'highlight'] = 'Today'
        filtered_spreads_regression.loc[filtered_spreads_regression.index == today - pd.Timedelta(weeks=1), 'highlight'] = 'Last Week'
        filtered_spreads_regression.loc[filtered_spreads_regression.index == today - pd.DateOffset(months=1), 'highlight'] = 'One Month Ago'

        # Set point sizes for highlights
        filtered_spreads_regression['size'] = np.where(filtered_spreads_regression['highlight'] == 'Other', 5, 15)

        col1, col2 = st.columns(2, gap="small")
        with col1:
            st.metric("Z4H5", filtered_spreads_transformed["z4h5"].iloc[-1].round(2),
                      (filtered_spreads_transformed["z4h5"].iloc[-1] - filtered_spreads_transformed["z4h5"].iloc[-2]).round(2))
            fig = px.line(filtered_spreads_transformed, y="z4h5_zscore" if display_zscores else "z4h5",
                          title="Z4H5")
            st.plotly_chart(fig)

            fig2 = px.line(filtered_spreads_transformed, y="z4m5_zscore" if display_zscores else "z4m5",
                           title="Z4M5")
            st.plotly_chart(fig2)

            fig3 = px.line(filtered_spreads_transformed, y="z4u5_zscore" if display_zscores else"z4u5",
            title = "Z4U5")
            st.plotly_chart(fig3)

        with col2:
            st.metric("Z4M5", filtered_spreads_transformed["z4m5"].iloc[-1].round(2),
            (filtered_spreads_transformed["z4m5"].iloc[-1] - filtered_spreads_transformed["z4m5"].iloc[-2]).round(2))
            
            # Regression plots (unmodified data)
            fig3 = px.scatter(
                filtered_spreads_regression, x = "z4", y="z4h5",
                color='highlight', trendline="ols",
                title="Z4H5",
            )
            st.plotly_chart(fig3)

            fig4 = px.scatter(
                filtered_spreads_regression, x = "z4",y="z4m5",
                color='highlight', trendline="ols",
                title="Z4M5",
            )
            st.plotly_chart(fig4)

            fig5 = px.scatter(
                filtered_spreads_regression, x= "z4", y = "z4u5",
                color = "highlight",trendline = "ols",
                title = "Z4U5",
            )
            st.plotly_chart(fig5)

