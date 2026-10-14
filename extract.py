# import os
# from dotenv import load_dotenv
# import requests
# import pandas as pd
# from sqlalchemy import create_engine

# load_dotenv()

# api_key = os.getenv('API_KEY')

# symbol = "IBM"
# # Note: Intraday function requires matching key format below
# url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}"

# print(f"Fetching data for {symbol}.....")
# response = requests.get(url)
# raw_data = response.json()

# # FIX 1: Changed "Time Series, (Daily)" to match the 5min URL query
# time_series = raw_data.get("Time Series (5min)", {})

# if not time_series:
#     print("Error: Could not retrieve time series data. Check your API limit or key.")
#     print(raw_data)
#     exit()
    
# print("Transforming JSON data....")
# cleaned_data = []

# for date_str, price_data in time_series.items():
#     # FIX 2: Replaced commas with periods in the dictionary keys
#     row = {
#         "symbol": symbol,
#         "date": date_str,
#         "open": float(price_data["1. open"]),
#         "high": float(price_data["2. high"]),
#         "low": float(price_data["3. low"]),
#         "close": float(price_data["4. close"]),
#         "volume": int(price_data["5. volume"])
#     }
#     cleaned_data.append(row)
    
# stock_df = pd.DataFrame(cleaned_data)
    
# # FIX 3: Added the missing string-to-datetime conversion
# stock_df['date'] = pd.to_datetime(stock_df['date'])




# db_user = os.getenv('DB_USER')
# db_password = os.getenv('DB_PASSWORD')
# db_host = os.getenv('DB_HOST')
# db_port = os.getenv('DB_PORT')
# db_name = os.getenv('DB_NAME')



# # 2. Create the SQLAlchemy connection engine for PostgreSQL
# # Format: postgresql+psycopg2://user:password@host:port/dbname
# connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
# engine = create_engine(connection_string)

# # 3. Load the DataFrame into PostgreSQL
# table_name = "stock_prices"
# print(f"Loading data into PostgreSQL table '{table_name}'...")


# try:
#     stock_df.to_sql(
#         name=table_name,
#         con=engine,
#         if_exists='append',
#         index=False,
#         chunksize=1000
#     )
#     print("Database upload successful!")
    
# except Exception as e:
#     print(f"An error occurred while uploading to the database: {e}")

# print("\nData Transformation Complete!")
# print(stock_df.info())
# print(stock_df.head())



import os
import sys
from dotenv import load_dotenv
import requests
import pandas as pd
from sqlalchemy import create_engine


# load environment variables at the module level

load_dotenv()


def fetch_stock_data(symbol: str, interval: str = "5min") -> dict:
    """
    EXTRACT: Fetches raw JSON data from Alpha Vantage for a given stock symbol.
    """
    api_key = os.getenv('API_KEY')
    if not api_key:
        print("Error: API_KEY is missing from environment varibles.")
        return {}
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={api_key}"
    
    print(f"Fetching data from {symbol} ({interval}).....")
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check http errors
        return response.json()
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return {}
    
    

def transform_stock_data(raw_data: dict, symbol: str, interval: str = "5min") -> pd.DataFrame:
    """
    TRANSFORM: Cleans Alpha Vantage JSON structure into a structured Pandas DataFrame.
    """
    # Dynamic key generation based on interval (e.g., 'Time Series (5min)'
    time_series_key = f"Time Series ({interval})"
    time_series = raw_data.get(time_series_key, {})
    
    if not time_series:
        print("Error: Could not retrieve time series data. Check your API limit or key.")
        print("API Response:", raw_data)
        return pd.DataFrame()  # Return empty DataFrame if extraction failed
    
    print("Transforming JSON data...")
    
    cleaned_data = []
    
    for date_str, price_data in time_series.items():
        row = {
            "symbol": symbol,
            "date": date_str,
            "open": float(price_data.get("1. open", 0)),
            "high": float(price_data.get("2. high", 0)),
            "low": float(price_data.get("3. low", 0)),
            "close": float(price_data.get("4. close", 0)),
            "volume": int(price_data.get("5. volume", 0))
        }
        
        cleaned_data.append(row)
        
        
    stock_df = pd.DataFrame(cleaned_data)
    
    if not stock_df.empty:
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        
    return stock_df


def load_data_to_postgres(stock_df: pd.DataFrame, table_name: str = "stock_prices") -> bool:
    """
    LOAD: Establishes a database engine and appends the DataFrame to PostgreSQL.
    """
    
    if stock_df.empty:
        print("Error: No data to load.")
        return False
    
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    
    
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"  
    
    print(f"Loading data into PostgresSQL table '{table_name}'")
    
    try:
        engine = create_engine(connection_string)
        stock_df.to_sql(
            name = table_name,
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        print("Database upload successful!")
        return True
        
    except Exception as e:
        print(f"An error occurred while uploading to the database: {e}")
        return False
    
    
def run_pipeline(symbol: str, interval: str = '5min'):
    """
    Orchestrate the entire pipeline
    """
    
    # 1. Extract
    raw_json = fetch_stock_data(symbol, interval)
    
    # 2. Transform
    my_stock_data = transform_stock_data(raw_json, symbol, interval)
    
    # 3. Load
    
    success = load_data_to_postgres(my_stock_data, table_name='stock_prices')
    
    
    if success:
        print(f"Pipeline completed successfully for {symbol}!")
        
    else:
        print(f"Pipeline failed for {symbol}.")
        
        
if __name__ == "__main__":
    TARGET_SYMBOL = "IBM"
    run_pipeline(symbol=TARGET_SYMBOL, interval="5min")
        

