import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


def get_unified_timeseries_data():
    """
    Connects to the database, aggregates daily sentiment (mean),
    merges it with commodity prices, and prepares a Time Series DataFrame.
    """

    print("Fetching and Aggregating Data from SQLite....")
    conn = sqlite3.connect("market_data.db")

    #joining on the basis of data
    query="""
        SELECT
            c.date,
            c.gold_price,
            c.silver_price,
            AVG(n.sentiment_score) as avg_sentiment,
            COUNT(n.headline) as news_volumne
            FROM commodity_metrics c
            LEFT JOIN news_sentiment n ON c.date = n.date
            GROUP BY c.date
            ORDER BY c.date ASC;
    """

    df_merged=pd.read_sql_query(query,conn)

    #preprocessing
    df_merged['date'] = pd.to_datetime(df_merged['date'])
    df_merged.set_index('date',inplace=True)
    df_merged.dropna(inplace=True)

    return df_merged

def plot_baseline_data(df):
    """
    Creates a basic plot to visualize the raw variables before applying SQC math.
    """
    print("Generating Basline Time-Series Plot....")

    #figure with 2 subplots (1 for prices, 1 for sentiment)
    fig,(ax1,ax2) = plt.subplots(2,1,figsize=(10,8),sharex=True)

    #plot 1: commodities
    ax1.plot(df.index,df['gold_price'],marker='o', color='gold', label='Gold Price')
    ax1.plot(df.index,df['silver_price'],marker='o', color='silver', label='Silver Price')
    ax1.set_title("Daily Price of Commodities")
    ax1.set_ylabel("Commodity Price (Rs)")
    ax1.legend()
    ax1.grid(True,linestyle="--",alpha=0.6)

    #plot 2 : average sentiment
    ax2.plot(df.index,df['avg_sentiment'], marker='o', color='blue', label='Avg Market Sentiment')
    ax2.set_title("Daily Average Banking News Sentiment")
    ax2.set_ylabel("Sentiment Score (-1 to +1)")
    ax2.set_xlabel("Date")
    ax2.axhline(0, color='red', linestyle='-', alpha=0.3) # 0 Neutral line
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()

def apply_sqc_math(df):
    """
    Calculates Mean (μ) and 3-Sigma Limits (μ ± 3σ) for Sentiment and Gold.
    """
    print("Calculating SQC Limits......\n")

    #sentiment sqc math
    sentiment_mean = df['avg_sentiment'].mean()
    sentiment_std = df['avg_sentiment'].std()

    df['sentiment_ucl']=sentiment_mean+(3*sentiment_std)
    df['sentiment_lcl']=sentiment_mean-(3*sentiment_std)
    df['sentiment_mean']=sentiment_mean

    #gold price sqc math
    gold_mean = df['gold_price'].mean()
    gold_std = df['gold_price'].std()

    df['gold_ucl'] = gold_mean+(3*gold_std)
    df['gold_lcl'] = gold_mean-(3*gold_std)
    df['gold_mean'] = gold_mean
    
    #silver price sqc math
    silver_mean = df['silver_price'].mean()
    silver_std = df['silver_price'].std()

    df['silver_ucl'] = silver_mean+(3*silver_std)
    df['silver_lcl'] = silver_mean-(3*silver_std)
    df['silver_mean'] = silver_mean
    
    print("-MARKET SENTIMENT STATISTICS-")
    print(f"Mean : {sentiment_mean:.4f}")
    print(f"Std Dev : {sentiment_std:.4f}")
    print(f"Upper Limit (UCL): {df['sentiment_ucl'].iloc[0]:.4f}")
    print(f"Lower Limit (LCL): {df['sentiment_lcl'].iloc[0]:.4f}\n")
    
    print("-GOLD PRICE STATISTICS-")
    print(f"Mean : Rs {gold_mean:.2f}")
    print(f"Std Dev : Rs {gold_std:.2f}")
    print(f"Upper Limit (UCL): Rs {df['gold_ucl'].iloc[0]:.2f}")
    print(f"Lower Limit (LCL): Rs {df['gold_lcl'].iloc[0]:.2f}\n")
    
    print("-SILVER PRICE STATISTICS-")
    print(f"Mean : Rs {silver_mean:.2f}")
    print(f"Std Dev : Rs {silver_std:.2f}")
    print(f"Upper Limit (UCL): Rs {df['silver_ucl'].iloc[0]:.2f}")
    print(f"Lower Limit (LCL): Rs {df['silver_lcl'].iloc[0]:.2f}\n")

    return df

def plot_control_charts(df):
    """
    Plots the final SQC Control Chart for Silver Prices, 
    dynamically highlighting statistical anomalies.
    """

    print("Generating SQC Control Charts.....")

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)

    #gold sqc chart
    ax1.plot(df.index,df['gold_price'],marker='o', color='gold', label='Gold Price', alpha=0.8)
    ax1.axhline(df['gold_mean'].iloc[0],color='green', linestyle='--', linewidth=2, label='Mean')
    ax1.axhline(df['gold_ucl'].iloc[0],color='red', linestyle='-', linewidth=2, label='UCL')
    ax1.axhline(df['gold_lcl'].iloc[0],color='red', linestyle='-', linewidth=2, label='LCL')

    #gold anomalies
    gold_anomalies = df[(df['gold_price']>df['gold_ucl'])|(df['gold_price']<df['gold_lcl'])]
    ax1.scatter(gold_anomalies.index, gold_anomalies['gold_price'], color='red', s=100, zorder=5,label='ANOMALY')
    ax1.set_title("Gold Price Stability Control Chart", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Price (Rs)", fontsize=12)
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)

    #silver sqc chart
    ax2.plot(df.index, df['silver_price'], marker='o', color='grey', label='Silver Price', alpha=0.7)
    ax2.axhline(df['silver_mean'].iloc[0], color='green', linestyle='--', linewidth=2, label='Mean (\u03bc)')
    ax2.axhline(df['silver_ucl'].iloc[0], color='red', linestyle='-', linewidth=2, alpha=0.6, label='UCL')
    ax2.axhline(df['silver_lcl'].iloc[0], color='red', linestyle='-', linewidth=2, alpha=0.6, label='LCL')
    
    #silver anomalies
    silver_anomalies = df[(df['silver_price'] > df['silver_ucl']) | (df['silver_price'] < df['silver_lcl'])]
    ax2.scatter(silver_anomalies.index, silver_anomalies['silver_price'], color='red', s=150, zorder=5, label='ANOMALY')
    ax2.set_title("Silver Market Shocks Control Chart", fontsize=14, fontweight='bold')
    ax2.set_ylabel("Price (Rs)", fontsize=12)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)

    # sentiment sqc chart
    ax3.plot(df.index, df['avg_sentiment'], marker='o', color='blue', label='Avg Sentiment', alpha=0.7)
    ax3.axhline(df['sentiment_mean'].iloc[0], color='green', linestyle='--', linewidth=2, label='Mean (\u03bc)')
    ax3.axhline(df['sentiment_ucl'].iloc[0], color='red', linestyle='-', linewidth=2, alpha=0.6, label='UCL')
    ax3.axhline(df['sentiment_lcl'].iloc[0], color='red', linestyle='-', linewidth=2, alpha=0.6, label='LCL')
    
    # sentiment anomalies
    sentiment_anomalies = df[(df['avg_sentiment'] > df['sentiment_ucl']) | (df['avg_sentiment'] < df['sentiment_lcl'])]
    ax3.scatter(sentiment_anomalies.index, sentiment_anomalies['avg_sentiment'], color='red', s=150, zorder=5, label='ANOMALY')
    ax3.set_title("Market News Sentiment Control Chart", fontsize=14, fontweight='bold')
    ax3.set_xlabel("Date", fontsize=12)
    ax3.set_ylabel("Sentiment Score", fontsize=12)
    ax3.legend()
    ax3.grid(True, linestyle='--', alpha=0.5)
    
    
    plt.tight_layout()
    plt.savefig('latest_chart.png', bbox_inches='tight')

if __name__ == "__main__":
    raw_df = get_unified_timeseries_data()
    
    print(raw_df)