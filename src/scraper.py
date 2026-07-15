import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    """
    Fetches the HTML content of a given URL using a custom User-Agent to bypass bot protection.
    """
    #defining the custom header to mimic a real web browser
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    #send the HTTP GET request to the target website
    print(f"Connecting to {url}...")
    response = requests.get(url,headers = headers)

    #checking if the connection was successful
    if response.status_code == 200:
        print("Connection Successful.")
        soup = BeautifulSoup(response.text,'html.parser')
        return soup
    else:
        print(f"Failed to Connect. Status Code: {response.status_code}")
        return None

def scrape_financial_news(url):
    """
    Scrapes a financial news webpage and filters headlines related to specific banks.
    """
    #setting up the target keywords
    target_banks = ['SBI','ICICI','HDFC']
    filtered_news=[]
    
    #to remove duplicates
    seen_titles = set()

    soup = fetch_html(url)

    if not soup:
        return filtered_news
    
    #finding all the <a> tags
    headlines = soup.find_all('a')

    for tag in headlines:
        title = tag.text.strip()
        link = tag.get('href',None)

        #checking the length of title and verifying bank names
        if title and len(title)>30:
            if any(bank.lower() in title.lower() for bank in target_banks):
                if title not in seen_titles:
                    seen_titles.add(title)
                    if link and link.startswith("/"):
                        link = "https://economictimes.indiatimes.com" + link
                    
                    filtered_news.append({
                        "Headline": title,
                        "Link":link
                    })
    return filtered_news

def scrape_commodity_prices():
    """
    Scrapes current ETF prices for Gold and Silver from Google Finance.
    """
    #urls from Google Finance for ETFS
    etf_urls = {
        'Gold':'https://www.google.com/finance/quote/GOLDBEES:NSE',
        'Silver': 'https://www.google.com/finance/quote/SILVERBEES:NSE'
    }
    
    prices_data = []

    for asset,url in etf_urls.items():
        soup = fetch_html(url)
        if not soup:
            continue

        price_element = soup.find("div",class_="N6SYTe")
        
        if price_element:
            raw_price = price_element.text.strip()
            clean_text = raw_price.replace('₹',"").replace(",","")
            clean_price = float(clean_text)
            
            prices_data.append({
                'Asset':asset,
                "Price":clean_price
            })
        else:
            #warning in case class is changed by the admin of the site
            print(f" ALERT: Price extraction failed for {asset} ETF.")
            print(f"   Reason: The CSS class might have been updated by Google Finance.")
            print(f"   Action: Open {url}, inspect the price element, and update the class name in scraper.py.")
    return prices_data

#testing   
if __name__ == "__main__":
    print("- Testing Commodity Prices....")
    prices = scrape_commodity_prices()
    for item in prices:
        print(f"{item['Asset']} ETF Price: Rs. {item['Price']}")
    
    print("- Testing Financial News....")
    test_url = "https://economictimes.indiatimes.com/industry/banking/finance/banking"
    bank_news = scrape_financial_news(test_url)
    for news in bank_news:
        print("-",news['Headline'].encode('ascii', 'ignore').decode('ascii'))