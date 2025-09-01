import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.title("IMDb List Scraper 🎬")

url = st.text_input("Pega la URL de IMDb aquí:")

def scrape_imdb(url):
    headers = {"Accept-Language": "en-US,en;q=0.8"}  # evita problemas con /es-es
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    movies = []

    # Detectar si es un "chart" (top 250) o una "list"
    rows = soup.select("ul.ipc-metadata-list li") or soup.select("tbody tr")

    for idx, row in enumerate(rows, start=1):
        title = row.select_one("h3") or row.select_one(".titleColumn a")
        year = row.select_one("span.ipc-metadata-list-summary-item__li") or row.select_one(".secondaryInfo")
        duration = row.find(string=lambda t: "min" in t)  # busca duración tipo "142 min"
        age = row.find(string=lambda t: "Rated" in t or "PG" in t or "R" in t)  # edad/restricción
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

    df = pd.DataFrame(movies)
    return df

if url:
    df = scrape_imdb(url)
    if df.empty:
        st.error("No se pudo extraer información de esta URL. Verifica que sea una lista de IMDb válida.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "imdb_list.csv", "text/csv")
