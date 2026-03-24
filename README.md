# WikiScraper
Python-based web scraper and data analysis CLI tool for extracting paragraphs, tables, and word frequencies from wikis.

## Features

* **Article Summarization (`--summary`)**: Extracts the first paragraph of an article and removes all HTML tags to provide pure text.
* **Table Extraction (`--table`)**: Locates a specific table within the article, extracts its content, and exports it to a structured `.csv` file.
* **Word Counting (`--count-words`)**: Counts all words within an article's content and saves the aggregated data into a `word-counts.json` file.
* **Automated Web Crawling (`--auto-count-words`)**: Traverses internal wiki links up to a specified depth to continuously update word frequency data.
* **Frequency Analysis (`--analyze-relative-word-frequency`)**: Compares the frequency of words found in the wiki articles against general language frequency data, with an option to generate comparison charts.

## Technologies Used

* **Python 3**
* **BeautifulSoup4**: For HTML parsing, DOM traversal, and pure text extraction.
* **Pandas**: For handling tabular data, generating CSV files, and managing datasets.
* **Requests**: For handling HTTP requests.
* **unittest**: For local unit and integration testing.

## Usage

Run the tool from the command line by providing the target phrase and the desired operation flag. 

**Example:**
```bash
python wiki_scraper.py --summary "Team Rocket"
