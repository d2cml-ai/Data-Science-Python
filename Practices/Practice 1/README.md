# Stock Analysis and Reddit Data Scraper

## Project Overview

This project is a multi-part Jupyter Notebook that demonstrates a full data pipeline, from web scraping and API data collection to analysis and portfolio construction.

*   **Exercise 1: Stock Portfolio Analysis**
    *   Scrapes the top 50 stock gainers from Yahoo Finance using `selenium`.
    *   Retrieves 12 months of historical stock price data for these companies using the `yfinance` library. [3]
    *   Constructs a portfolio by selecting the top 10 stocks based on their cumulative returns in the first 6 months.
    *   Analyzes the performance of this equal-weighted portfolio over the subsequent 5 months.

*   **Exercise 2: Reddit Data Collection**
    *   Connects to the Reddit API using the Python Reddit API Wrapper (`praw`). [19]
    *   Collects the top 20 "hot" posts from the subreddits: `r/politics`, `r/PoliticalDiscussion`, and `r/worldnews`.
    *   Fetches the top 5 comments for each of the collected posts.
    *   Merges the post and comment data into a single, structured pandas DataFrame.

## Features

- **Web Scraping**: Utilizes `selenium` with headless browsing and anti-bot detection measures to reliably scrape data from dynamic web pages.
- **Financial Data API**: Leverages `yfinance` to efficiently download historical market data for multiple stock tickers. [6]
- **Portfolio Analysis**: Implements a quantitative strategy for stock selection and evaluates portfolio performance over time.
- **Reddit API Integration**: Demonstrates how to authenticate and collect data from the Reddit API using `praw`. [20]
- **Data Structuring**: Employs the `pandas` library for effective data manipulation, cleaning, and merging.


