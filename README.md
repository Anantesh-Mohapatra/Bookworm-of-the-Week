# Welcome to Bookworm of the Week!

This project scrapes the categories of the New York Times bestsellers list, and then uses the New York Times API to find the weekly bestsellers list for the categories. Additional data, from Goodreads and isbnsearch.org, is also added. The end product is a database for the week's bestsellers list, with information on Weeks on List, Stars, Reviews, and more.
This dataset is particularly helpful because it proves more topical data than other publicly available datasets, which cover a wider period of time but not as recent. 

Before running this code, you will need to get an API key for the New York Times. You can get an [API key here] (https://developer.nytimes.com/get-started).

How to Use the Program:
1. First, clone the repository to your local machine.
2. Create and activate a virtual environment to manage dependencies.
3. Install all the required Python packages by running requirements.txt.
4. Execute the script to start the scraping process.
5. The database will be exported as a .csv file.