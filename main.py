## Part 0 - Getting Set Up

# Import functions and libraries
import requests
from bs4 import BeautifulSoup
import random
import time
import os
from dotenv import load_dotenv
import pandas as pd
import re

# Headers to mimic a browser request
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# URL for finding the New York Times bestsellers
url = "https://www.nytimes.com/books/best-sellers/"

# Get API keys
load_dotenv()
NYT_API_KEY = os.getenv('NYT_API_KEYS')

if NYT_API_KEY:
    print(f"The API key is found.")
else:
    print("No API key found in the environment variables.")



## Part 1 - New York Times bestsellers categories

# Get the categories of the New York Times bestsellers
def scrape_bestseller_categories(url):
    response = requests.get(url, headers=headers)

    # If we get a 429 error (rate limiting), wait and retry
    if response.status_code == 429:
        print("Rate limit hit. Sleeping for a bit...")
        time.sleep(10)
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to get the webpage: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Create dictionary of categories
    book_categories = {}

    # Find all list items (li) under the unordered list (ul)
    list_items = soup.find_all('li', class_='css-108lmbq')

    for item in list_items:
        # Get the link text (e.g., "Combined Print & E-Book Nonfiction")
        link_text = item.a.get_text()
        
        # Get the href attribute (link URL)
        link_url = item.a['href']
        
        # Extract the second to last element from the URL path
        parts = link_url.split("/")
        if len(parts) > 2:
            new_key = parts[-2]
        
        # Store the new key and a list of the subcategory name and URL in the dictionary
        book_categories[new_key] = [link_text, link_url]
    
    return book_categories



## Part 2 - Get New York Times bestsellers list using the category

def get_nyt_book_data(category):
    # Before using the API, the category name must be formatted.
    formatted_category = category.replace(",", "").replace("&", "and").replace(" ", "-").lower()
    
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{formatted_category}.json?api-key={NYT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        nyt_book_data = response.json()
        
        # Extract relevant data from the JSON response
        books_list = nyt_book_data['results']['books']
        books_data = []

        for book in books_list:
            books_data.append({
                'Category': categories[category][0],
                'Title': book['title'],
                'Author': book['author'],
                'Rank': book['rank'],
                'Weeks on List': book['weeks_on_list'],
                'Publisher': book['publisher'],
                'ISBN13': next(isbn['isbn13'] for isbn in book['isbns']),
                'ISBN10': next(isbn['isbn10'] for isbn in book['isbns']),
                'Description': book['description']
            })

        # Create a DataFrame from the books_data list
        df = pd.DataFrame(books_data)

        return df
        
    else:
        print(f"Error: {response.status_code}")
        return None
    


## Part 3 - Get Book Price
# This gets the price of the book. The New York Times API is supposed to get the price, but that feature doesn't actually work (always returns 0.00)
def get_price(isbn):
    url = f'https://isbnsearch.org/isbn/{isbn}'
    response = requests.get(url, headers=headers)
    
    # If we get a 429 error (rate limiting), wait and retry
    if response.status_code == 429:
        print("Rate limit hit. Sleeping for a bit...")
        time.sleep(10)
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to get the webpage: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    price_link = soup.find("p", class_="pricelink")
        
    if price_link:
        # Extract and return the price inside the 'a' tag
        price_text = price_link.find("a").get_text(strip=True)
        price = float(price_text.replace("$", ""))
        return price
    
    else:
        return "Price not found on the page."



## Part 4 - Goodreads
# The Goodreads API is no longer publicly available - this gets details from Goodreads.
def get_goodreads_stats(isbn):
    url = f"https://www.goodreads.com/search?q={isbn}"
    response = requests.get(url, headers=headers)

    # If we get a 429 error (rate limiting), wait and retry
    if response.status_code == 429:
        print("Rate limit hit. Sleeping for a bit...")
        time.sleep(10)
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to get the webpage: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')

    stats_container = soup.find("div", class_="BookPageMetadataSection__ratingStats")

    goodread_stats = {}

    if stats_container:
        stars = float(soup.find("div", class_ = "RatingStatistics__rating").get_text(strip=True))
        review_text = soup.find("span", {"data-testid": "reviewsCount"}).get_text(strip=True)
        reviews = float(re.sub(r"[^\d.]", "", review_text)) # Needed to remove words from the reviews count
        ratings_text = soup.find("span", {"data-testid": "ratingsCount"}).get_text(strip=True)
        ratings = float(re.sub(r"[^\d.]", "", ratings_text)) # Needed to remove words from the ratings count
    
    else:
        print(f"Could not find Goodread stats. This is the isbn: {isbn}")
        stars = None
        reviews = None
        ratings = None
    
    stats = [stars, reviews, ratings]
    goodread_stats[isbn] = stats

    return goodread_stats



## Part 5.1 - Putting it together (adding additional details)
# This adds the new details from Goodreads and isbnsearch.org to the dataframe.
def get_add_details(df):
    prices = []
    stars_list = []
    reviews = []
    ratings = []
    for isbn in df['ISBN13']:
        # Get the additional details
        price = get_price(isbn)
        
        goodreads_stats = get_goodreads_stats(isbn)
        stars = goodreads_stats[isbn][0]
        review_count = goodreads_stats[isbn][1]
        ratings_count = goodreads_stats[isbn][2]

        # Add new details to a list
        prices.append(price)
        stars_list.append(stars)
        reviews.append(review_count)
        ratings.append(ratings_count)

    df['Price'] = prices
    df['Stars'] = stars_list
    df['Reviews'] = reviews
    df['Ratings'] = ratings

    return df



## Part 5.2 - Putting it together (processing all categories)
def get_data_for_mult_categories(url):
    # Get categories
    categories = scrape_bestseller_categories(url)
    category_list = categories.keys()
    book_dataframe = pd.DataFrame()
    for category in category_list:
        df_cat = get_nyt_book_data(category)
        df_cat = get_add_details(df_cat)
        book_dataframe = pd.concat([book_dataframe, df_cat], ignore_index=True)
    
    return book_dataframe


## THIS IS WHERE THE CODE STARTS ##
## Running the code:
book_dataframe = get_data_for_mult_categories(url)
book_dataframe.to_csv("bookworm_of_the_week.csv")
