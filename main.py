import src.scraper as scraper
import src.analyzer as analyzer
import src.database as database
import subprocess
import analysis as analysis
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

load_dotenv()

def run_pipeline():
    """
    Executes the ETL (Extract, Transform, Load) pipeline.
    Currently orchestrates Phase 1 (Extraction) and Phase 2 (Transformation).
    """
    print("Starting Data Pipeline....")

    #extracting raw data
    print("Scraping live market data....")

    news_url = "https://economictimes.indiatimes.com/industry/banking/finance/banking"
    raw_news_data = scraper.scrape_financial_news(news_url)
    raw_prices_data=scraper.scrape_commodity_prices()

    headlines_list = [item['Headline'] for item in raw_news_data]

    
    gold_price = 0.0
    silver_price =0.0

    for item in raw_prices_data:
        if item['Asset'] == 'Gold':
            gold_price = item['Price']
            
        elif item['Asset'] == 'Silver':
            silver_price = item['Price']

    print(f"-> Scraped {len(headlines_list)} banking headlines.")
    print(f"-> Gold ETF: Rs {gold_price}, Silver ETF: Rs {silver_price}")

    #transforming into dataframe
    final_market_df=analyzer.create_market_dataframe(
        headlines=headlines_list,
        gold_price =gold_price,
        silver_price = silver_price
    )
    
    #loading the data into database
    print("Saving Data to SQLite Database.....")
    database.setup_database()
    database.save_market_data(final_market_df)

    return final_market_df

def generate_live_dashboard(df):
    print("Generating Live HTML Dashboard with Statistical Scorecard...")
    now = datetime.now()
    timestamp_str = now.strftime("%d %B %Y, %I:%M %p")
    
    
    latest_data = df.iloc[-1]
    
    gold_price = round(latest_data['gold_price'], 2)
    gold_mean = round(latest_data['gold_mean'], 2)
    gold_ucl = round(latest_data['gold_ucl'], 2)
    gold_lcl = round(latest_data['gold_lcl'], 2)
    
    silver_price = round(latest_data['silver_price'], 2)
    silver_mean = round(latest_data['silver_mean'], 2)
    silver_ucl = round(latest_data['silver_ucl'], 2)
    silver_lcl = round(latest_data['silver_lcl'], 2)
     
    sentiment_score = round(latest_data['avg_sentiment'], 4)
    sentiment_mean = round(latest_data['sentiment_mean'], 4)
    sentiment_ucl = round(latest_data['sentiment_ucl'], 4)
    sentiment_lcl = round(latest_data['sentiment_lcl'], 4)
    
    sentiment_status = "🔴 BREACH" if (sentiment_score > sentiment_ucl or sentiment_score < sentiment_lcl) else "🟢 NORMAL"
    gold_status = "🔴 BREACH" if (gold_price > gold_ucl or gold_price < gold_lcl) else "🟢 NORMAL"
    silver_status = "🔴 BREACH" if (silver_price > silver_ucl or silver_price < silver_lcl) else "🟢 NORMAL"
    
    
    if "BREACH" in gold_status or "BREACH" in silver_status or "BREACH" in sentiment_status:
        exec_summary = "<span style='color: #e74c3c; font-weight: bold;'>CRITICAL ALERT:</span> Market anomaly detected today. Prices have breached the 3-Sigma statistical boundaries."
    else:
        exec_summary = "<span style='color: #27ae60; font-weight: bold;'>ALL CLEAR:</span> Both Gold and Silver are trading smoothly within expected statistical control limits."

  
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Market SQC Dashboard</title>
        <style>
            :root {{
                --primary: #2c3e50;
                --secondary: #34495e;
                --bg-color: #f4f7f6;
                --box-bg: #ffffff;
                --text-main: #333;
                --text-muted: #7f8c8d;
                --border-light: #e0e6ed;
            }}
            
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background-color: var(--bg-color); 
                color: var(--text-main); 
                padding: 15px; 
                line-height: 1.6;
            }}
            
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background: var(--box-bg); 
                padding: 25px; 
                border-radius: 12px; 
                box-shadow: 0 8px 24px rgba(0,0,0,0.08); 
            }}
            
            h1 {{ 
                text-align: center; 
                color: var(--primary); 
                font-size: clamp(1.8rem, 4vw, 2.5rem); 
                margin-bottom: 5px; 
            }}
            
            .timestamp {{ 
                text-align: center; 
                font-size: clamp(0.9rem, 2vw, 1.1rem); 
                color: var(--text-muted); 
                font-weight: 500; 
                margin-bottom: 25px; 
            }}
            
            .summary-box {{ 
                background: #fdfefe; 
                border-left: 6px solid var(--secondary); 
                padding: 15px 20px; 
                margin-bottom: 30px; 
                font-size: clamp(1rem, 2vw, 1.15rem); 
                border-radius: 6px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
            }}
            
            /* Responsive Table Wrapper */
            .table-responsive {{
                width: 100%;
                overflow-x: auto;
                margin-bottom: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }}
            
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                min-width: 700px; /* Forces scroll on very small screens instead of squishing */
                background: white;
            }}
            
            th, td {{ 
                padding: 16px 12px; 
                text-align: center; 
                border-bottom: 1px solid var(--border-light); 
                font-size: clamp(0.9rem, 1.5vw, 1.05rem);
            }}
            
            th {{ 
                background-color: var(--secondary); 
                color: white; 
                font-weight: 600; 
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            tr:hover {{ background-color: #f8f9fa; }}
            tr:last-child td {{ border-bottom: none; }}
            
            /* Highlight the new Sentiment Row */
            .sentiment-row {{
                background-color: #f4f6f7;
                border-top: 2px solid var(--secondary);
            }}
            
            .chart-container {{ 
                text-align: center; 
                margin-bottom: 30px; 
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid var(--border-light);
            }}
            
            .chart-container h3 {{
                text-align: left;
                margin-bottom: 15px;
                color: var(--primary);
                font-size: 1.3rem;
            }}
            
            img {{ 
                max-width: 100%; 
                height: auto; 
                border-radius: 6px; 
                display: block;
                margin: 0 auto;
            }}
            
            .footer {{ 
                text-align: center; 
                font-size: 0.9rem; 
                color: var(--text-muted); 
                border-top: 1px solid var(--border-light); 
                padding-top: 20px; 
                margin-top: 20px;
            }}
            
            .footer strong {{ color: var(--primary); }}

            /* Mobile Specific Adjustments */
            @media (max-width: 768px) {{
                .container {{ padding: 15px; }}
                th, td {{ padding: 12px 8px; }}
                .summary-box {{ padding: 12px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Market Sentiment Tracker (Automated)</h1>
            <div class="timestamp">Live Data Refreshed: {timestamp_str}</div>
            
            <!-- 1. Executive Summary -->
            <h3>Executive Summary</h3>
            <div class="summary-box">
                {exec_summary}
            </div>
            
            <!-- 2. Statistical Scorecard -->
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Metric / Asset</th>
                            <th>Current Value</th>
                            <th>Mean</th>
                            <th>LCL</th>
                            <th>UCL</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Gold ETF (Rs)</strong></td>
                            <td>{gold_price}</td>
                            <td>{gold_mean}</td>
                            <td>{gold_lcl}</td>
                            <td>{gold_ucl}</td>
                            <td>{gold_status}</td>
                        </tr>
                        <tr>
                            <td><strong>Silver ETF (Rs)</strong></td>
                            <td>{silver_price}</td>
                            <td>{silver_mean}</td>
                            <td>{silver_lcl}</td>
                            <td>{silver_ucl}</td>
                            <td>{silver_status}</td>
                        </tr>
                        <!-- NEW: Market Sentiment Row -->
                        <tr class="sentiment-row">
                            <td><strong>Banking News Sentiment</strong></td>
                            <td>{sentiment_score}</td>
                            <td>{sentiment_mean}</td>
                            <td>{sentiment_lcl}</td>
                            <td>{sentiment_ucl}</td>
                            <td>{sentiment_status}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- 3. Visual Proof (Control Charts) -->
            <div class="chart-container">
                <h3>Statistical Variance Visualization by SQC</h3>
                <img src="latest_chart.png" alt="SQC Control Chart">
            </div>
            
            <!-- 4. Technical Architecture -->
            <div class="footer">
                Built by <strong>Shaurya Sinha</strong><br>
                <em>Automated via Python ETL, SQLite, and GitHub Actions/Pages Ecosystem.</em>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    print("index.html created and populated with statistical data successfully.")

def push_to_github():
    print("Pushing updates to GitHub...")
    try:
        subprocess.run(["git", "add", "index.html", "latest_chart.png"], check=True)
        commit_message = f"Automated Daily Market Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Dashboard deployed to GitHub Pages.")
    except subprocess.CalledProcessError as e:
        print(f"Git Automation Failed: {e}")

def send_executive_email():
    print("Sending Executive Email Notification...")
    
    
    SENDER_EMAIL = "shauryasinhaop@gmail.com" 
    RECEIVER_EMAIL = "shauryasinha070@gmail.com" 
    LIVE_URL = "https://shaurya-portfolio.github.io/market-sentiment-tracker/" 
    
    SENDER_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    
    if not SENDER_APP_PASSWORD:
        print("Error: GMAIL_APP_PASSWORD not found in .env file.")
        return
    
    msg = EmailMessage()
    msg['Subject'] = f"MARKET SQC: Daily Report Live ({datetime.now().strftime('%d %b')})"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    email_body = f"""
    Mr. Shaurya,
    
    The Python ETL pipeline has successfully executed. 
    New market data has been ingested and the dashboard has been updated.
    
    Access the live statistical report here: {LIVE_URL}
    
    Regards,
    Automated Python Pipeline
    {datetime.now().strftime('%d %b')}
    """
    msg.set_content(email_body)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp.send_message(msg)
        print("Success email delivered.")
    except Exception as e:
        print(f"Email sending failed: {e}")


if __name__ == "__main__":
    print("=== STARTING DAILY ETL PIPELINE ===\n")
    
    # ==========================================
    # ACTUAL EXECUTION BLOCK 
    # ==========================================
    # Jab tum ready ho, in lines se '#' hata dena:
    run_pipeline()
    raw_df = analysis.get_unified_timeseries_data()
    sqc_df = analysis.apply_sqc_math(raw_df)
    analysis.plot_control_charts(sqc_df)

     
    
    # Dhyan do! generate_live_dashboard ab sqc_df as an argument accept karta hai
    generate_live_dashboard(sqc_df)
    
    push_to_github()
    send_executive_email()
    
    print("\n=== PIPELINE EXECUTION COMPLETE ===")