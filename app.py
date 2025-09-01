import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

st.title("IMDb Movie List Scraper 🎬")

# Default IMDb Top 250 URL
default_url = "https://www.imdb.com/chart/top/"

st.markdown(
    f"👉 You can scrape directly from the IMDb Top 250 list here: "
    f"[{default_url}]({default_url})"
)

url = st.text_input("Paste any IMDb list URL below:", value=default_url)

def scrape_imdb(url):
    headers = {"Accept-Language": "en-US,en;q=0.8"}  
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    movies = []

    # Try both IMDb structures (chart / list)
    rows = soup.select("ul.ipc-metadata-list li") or soup.select("tbody tr")

    progress = st.progress(0)
    total = len(rows) if rows else 1

    for idx, row in enumerate(rows, start=1):
        title = row.select_one("h3") or row.select_one(".titleColumn a")
        year = row.select_one("span.ipc-metadata-list-summary-item__li") or row.select_one(".secondaryInfo")
        duration = row.find(string=lambda t: "min" in t)  
        age = row.find(string=lambda t: any(r in t for r in ["Rated", "PG", "R", "G"]))  
        rating = row.select_one("span.ipc-rating-star--rating") or row.select_one(".imdbRating strong")
        votes = row.select_one("span.ipc-rating-star--voteCount") or (rating and rating.get("title"))

        movies.append({
            "No.": idx,
            "Title": title.get_text(strip=True) if title else "",
            "Year": year.get_text(strip=True).strip("()") if year else "",
            "Duration": duration.strip() if duration else "",
            "Age": age.strip() if age else "",
            "Rating": rating.get_text(strip=True) if rating else "",
            "Votes": votes.get_text(strip=True) if votes else ""
        })

        # Update progress bar
        progress.progress(min(idx / total, 1.0))

        # Small delay to make progress visible
        time.sleep(0.01)

    return pd.DataFrame(movies)

if url:
    df = scrape_imdb(url)
    if df.empty:
        st.error("Could not extract data from this URL. Please check that it is a valid IMDb list.")
    else:
        st.success("✅ Scraping completed!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "imdb_list.csv", "text/csv")
