## WineELO

In this repository, we explore an alternative to star ratings systems: the WineELO score. We scrape user (star) ratings from wine review platform Vivino, and convert them to WineELO scores to explore the merit of this new metric. 

This repository contains the following files:

- **wine_elo.ipynb**: notebook containing analysis
- **wine_data_cleanup.py**: python module with custom functions used in notebook
- **web_scraper.py**: web scraper used to retrieve Vivino user reviews

The dataset of scraped Vivino ratings have been been omitted from this repository due to size constraints. You may scrape data yourself by running web_scraper.py. Please note that you will need to download the appropriate version of chromedriver (https://chromedriver.chromium.org/downloads) to run this script. 

### Technologies
- Python
- Jupyter Notebook

### Getting Started

1. Clone this repo
2. Install the appropriate version of chromedriver and the executable to your PATH
3. Run web_scraper.py to get a full and fresh set of Vivino wine reviews
4. Run wine_elo.ipynb to run the analysis notebook

### Authors

Roald Schuring

