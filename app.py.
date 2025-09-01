# app.py
# -*- coding: utf-8 -*-
"""
Streamlit IMDb List Scraper
-------------------------------------------------
- Pega una URL de un listado de IMDb (ej.: https://www.imdb.com/chart/top/)
- Hace scraping de la página y extrae: título, año, rating, votos
- Muestra una tabla ordenable y permite descargar un Excel formateado

Librerías: requests, BeautifulSoup, pandas, openpyxl, streamlit
"""

import re
import io
import time
from typing import List, Dict, Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ---------------------- CONFIG ----------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 25
SLEEP_BETWEEN = 0.05
MAX_COL_WIDTH = 50

# ---------------------- HELPERS ----------------------

def _get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def _clean_year(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(19\d{2}|20\d{2}|21\d{2})", text)
    return int(m.group(1)) if m else None

def _clean_float(x: Optional[str]) -> Optional[float]:
    try:
        return float(str(x).strip())
    except Exception:
        return None

def _clean_votes(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    t = re.sub(r"[^0-9]", "", text)
    return int(t) if t else None

# ---------------------- PARSERS ----------------------

def parse_chart_table(soup: BeautifulSoup) -> List[Dict]:
    rows: List[Dict] = []
    table = soup.find("table", class_=lambda c: c and "chart" in c)
    if not table:
        return rows
    for tr in table.select("tbody tr"):
        title_td = tr.find("td", class_=lambda c: c and "titleColumn" in c)
        if not title_td:
            continue
        a = title_td.find("a")
        title = a.get_text(strip=True) if a else None
        year_span = title_td.find("span", class_=lambda c: c and "secondaryInfo" in c)
        year = _clean_year(year_span.get_text(strip=True) if year_span else None)

        rating_td = tr.find("td", class_=lambda c: c and "imdbRating" in c)
        rating = None
        votes = None
        if rating_td:
            strong = rating_td.find("strong")
            rating = _clean_float(strong.get_text(strip=True) if strong else None)
            if strong and strong.has_attr("title"):
                m = re.search(r"([0-9,\.]+)", strong["title"])
                if m:
                    votes = _clean_votes(m.group(1))

        if not title:
            continue
        rows.append({
            "title": title,
            "year": year,
            "rating": rating,
            "votes": votes,
        })
    return rows

def parse_lister_items(soup: BeautifulSoup) -> List[Dict]:
    rows: List[Dict] = []
    container = soup.find("div", class_=lambda c: c and "lister-list" in c)
    if not container:
        return rows
    for item in container.select("div.lister-item"):
        header = item.find("h3", class_=lambda c: c and "lister-item-header" in c)
        title = None
        year = None
        if header:
            a = header.find("a")
            title = a.get_text(strip=True) if a else None
            y = header.find("span", class_=lambda c: c and "lister-item-year" in c)
            year = _clean_year(y.get_text(strip=True) if y else None)

        rating = None
        rating_block = item.find("div", class_=lambda c: c and "ratings-imdb-rating" in c)
        if rating_block:
            strong = rating_block.find("strong")
            rating = _clean_float(strong.get_text(strip=True) if strong else None)

        votes = None
        nv = item.select_one("p.sort-num_votes-visible span[name='nv']")
        if nv:
            votes = _clean_votes(nv.get_text(strip=True))

        if title:
            rows.append({
                "title": title,
                "year": year,
                "rating": rating,
                "votes": votes,
            })
    return rows

def parse_ipc_modern_list(soup: BeautifulSoup) -> List[Dict]:
    rows: List[Dict] = []
    for li in soup.select("li.ipc-metadata-list-summary-item"):
        title_link = li.select_one("a.ipc-title-link-wrapper")
        title = None
        year = None
        if title_link:
            text = title_link.get_text(" ", strip=True)
            text = re.sub(r"^\d+\.\s*", "", text).strip()
            year_span = li.find("span", string=re.compile(r"\(\d{4}\)"))
            year = _clean_year(year_span.get_text(strip=True) if year_span else None)
            title = text

        rating = None
        votes = None
        star = li.select_one("span.ipc-rating-star--rating")
        if star:
            rating = _clean_float(star.get_text(strip=True))
        vc = li.select_one("span.ipc-rating-star--voteCount")
        if vc:
            votes = _clean_votes(vc.get_text(strip=True))

        if title:
            rows.append({
                "title": title,
                "year": year,
                "rating": rating,
                "votes": votes,
            })
    return rows

def scrape_imdb_list(url: str) -> pd.DataFrame:
    soup = _get_soup(url)
    parsers = [parse_chart_table, parse_lister_items, parse_ipc_modern_list]
    all_rows: List[Dict] = []
    for fn in parsers:
        rows = fn(soup)
        if rows:
            all_rows = rows
            break

    df = pd.DataFrame(all_rows, columns=["title", "year", "rating", "votes"]) if all_rows else pd.DataFrame(columns=["title", "year", "rating", "votes"])
    df.dropna(how="all", inplace=True)
    if not df.empty and "rating" in df.columns:
        df.sort_values(by=["rating", "votes"], ascending=[False, False], inplace=True, na_position="last")
        df.reset_index(drop=True, inplace=True)
    return df

def _to_styled_excel_bytes(df: pd.DataFrame, sheet_name: str = "IMDb List") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    headers = list(df.columns)
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    body_align = Alignment(vertical="top", wrap_text=True)
    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border
    ws.row_dimensions[1].height = 22

    for _, row in df.iterrows():
        ws.append(list(row.values))

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.alignment = body_align
            cell.border = border

    for col_idx, col_name in enumerate(headers, start=1):
        max_len = len(col_name)
        for cell in ws.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2, max_row=ws.max_row):
            for c in cell:
                if c.value is not None:
                    max_len = max(max_len, len(str(c.value)))
        ws.column_dimensions[chr(64 + col_idx)].width = min(max_len + 2, MAX_COL_WIDTH)

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()

# ---------------------- STREAMLIT UI ----------------------
st.set_page_config(page_title="IMDb List Scraper", page_icon="🎬", layout="wide")

st.title("🎬 IMDb List Scraper")
st.caption("Pega la URL de un listado de IMDb y obtén una tabla limpia + descarga en Excel.")

example_url = "https://www.imdb.com/chart/top/"
url = st.text_input("URL de IMDb (listado)", value=example_url)

colA, colB = st.columns([1, 3])
with colA:
    start = st.button("Extraer datos")
with colB:
    info = st.empty()

if start:
    if not url.strip():
        st.error("Por favor ingresa una URL de IMDb válida.")
        st.stop()

    info.info("Descargando y parseando la página...")
    t0 = time.time()
    try:
        df = scrape_imdb_list(url.strip())
    except Exception as e:
        st.error(f"Error al procesar la URL: {e}")
        st.stop()

    elapsed = time.time() - t0
    info.success(f"Listo en {elapsed:.2f}s — {len(df):,} filas")

    if df.empty:
        st.warning("No se encontraron elementos reconocibles en esta URL.")
    else:
        st.subheader("Resultados")
        st.dataframe(df, use_container_width=True, hide_index=True)

        xlsx_bytes = _to_styled_excel_bytes(df)
        st.download_button(
            label="⬇️ Descargar Excel",
            data=xlsx_bytes,
            file_name="imdb_list.xlsx",
            mime=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        )

st.markdown("---")
st.caption("Tips: si IMDb cambia su HTML, ajusta los selectores en los parsers.")
