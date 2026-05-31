# AI Web Scraper Agent - Test Scenarios Guide

This guide contains curated sandbox websites and high-quality prompts to help you test the AI Web Scraper Agent. These scenarios showcase the capabilities of parallel crawling, semantic selector trimming, and GPT-4o-mini structured data extraction.

---

## 1. Books Store Sandbox (E-commerce Layout)
Perfect for testing multi-page crawling, visual thumbnails rendering, and pricing details.

* **Target URL**: `https://books.toscrape.com`
* **Optimal Page Limit**: `1 to 5 pages`
* **Download Images Option**: `Checked (True)`
* **Recommended Prompts**:
  * > "Extract all books listed on the page. For each book, extract its: title, price, rating, availability status (in stock or out of stock), and cover image URL."
  * > "Find all books. Extract only the book title and its price in pounds."

---

## 2. Quotes Sandbox (Textual & Tag Layout)
Ideal for testing text-heavy structures, lists, and metadata tags parsing.

* **Target URL**: `https://quotes.toscrape.com`
* **Optimal Page Limit**: `1 to 3 pages`
* **Download Images Option**: `Unchecked (False)`
* **Recommended Prompts**:
  * > "Extract all quotes on the page. For each quote, capture: the quote text, the author's name, and a comma-separated list of tags."
  * > "Extract quotes that have the tag 'inspirational'. Capture quote text and the author."

---

## 3. Fake Python Jobs (Job Board Directory Layout)
Great for testing career directories, locations, and deadlines.

* **Target URL**: `https://realpython.github.io/fake-jobs/`
* **Optimal Page Limit**: `1 page`
* **Download Images Option**: `Unchecked (False)`
* **Recommended Prompts**:
  * > "Extract all job listings on the page. For each job, find: job title, company name, location, and the date posted."
  * > "Find all jobs listed. Extract the job title and the exact city and state location."

---

## 4. Largest Companies by Revenue (Wikipedia Tabular Data)
Perfect for testing high-density tables, complex numbers, and country attributes.

* **Target URL**: `https://en.wikipedia.org/wiki/List_of_largest_companies_by_revenue`
* **Optimal Page Limit**: `1 page`
* **Download Images Option**: `Unchecked (False)`
* **Recommended Prompts**:
  * > "Extract the table of the largest companies by revenue. For each company, capture: rank, company name, industry, revenue (in USD billions), profit, and headquarters location."

---

## How to Test on the Dashboard
1. Open the Premium Dashboard at **`https://web.scrapping.rasuonline.in`** (or localhost).
2. Copy and paste one of the **Target URLs** from above.
3. Paste the matching **Recommended Prompt** in the instructions box.
4. Set the **Page Limit** and toggle **Download Images** based on the scenario recommendations.
5. Click **Scrape Website** and watch the live progress tracker compile your styled Excel spreadsheet!

---
*Created by Antigravity Web Scraper Agent*
