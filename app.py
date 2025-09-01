import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

st.set_page_config(page_title="IMDb List Scraper", layout="wide")

st.title("🎬 IMDb List Scraper")
st.caption("Extrae datos de listas de IMDb y descárgalos en Excel")

url = st.text_input("Pega la URL de la lista de IMDb:")

def parse_imdb_list(url):
    headers = {"Accept-Language": "en-US,en;q=0.5"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error("No se pudo acceder a la página. Verifica la URL.")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    data = []

    items = soup.find_all("div", class_="ipc-metadata-list-summary-item")
    if not items:
        st.error("No se encontraron elementos. Puede que el diseño de IMDb haya cambiado.")
        return pd.DataFrame()

    for idx, item in enumerate(items, start=1):
        # Título
        title_tag = item.find("a", class_="ipc-title-link-wrapper")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Año, duración y edad
        metadata = item.find("span", class_="dli-title-metadata")
        year, duration, age = "", "", ""
        if metadata:
            parts = [m.get_text(strip=True) for m in metadata.find_all("span")]
            if len(parts) >= 1:
                year = parts[0]
            if len(parts) >= 2:
                duration = parts[1]
            if len(parts) >= 3:
                age = parts[2]

        # Rating
        rating_tag = item.find("span", class_="ipc-rating-star--rating")
        rating = rating_tag.get_text(strip=True) if rating_tag else ""

        # Votes
        votes_tag = item.find("span", class_="ipc-rating-star--voteCount")
        votes = votes_tag.get_text(strip=True).replace("(", "").replace(")", "") if votes_tag else ""

        data.append({
            "No.": idx,
            "Title": title,
            "Year": year,
            "Duration": duration,
            "Age": age,
            "Rating": rating,
            "Votes": votes
        })

    return pd.DataFrame(data)

def to_excel(df):
    wb = Workbook()
    ws = wb.active
    ws.title = "IMDb Data"

    # Encabezados
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Formato
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

if url:
    df = parse_imdb_list(url)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

        excel_data = to_excel(df)
        st.download_button(
            label="⬇️ Descargar Excel",
            data=excel_data,
            file_name="imdb_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
