import httpx
import json
import re
from bs4 import BeautifulSoup
import streamlit as st
import requests
import time

class JournalScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        }
        self.session = requests.Session()

    def get_articles_from_url(self, url):
        try:
            if not url.startswith('http'):
                url = f'https://{url}'

            st.write(f"Accediendo a: {url}")

            response = self.session.get(url, headers=self.headers)
            st.write(f"Status code: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []

            # Buscar todas las secciones que contienen PDF links
            pdf_links = soup.find_all('a', href=lambda x: x and 'files.jofph.com/files/article' in x and '.pdf' in x)
            st.write(f"PDF links encontrados: {len(pdf_links)}")

            for pdf_link in pdf_links:
                try:
                    # Encontrar el contenedor del artículo (el padre que contiene toda la info)
                    article_container = pdf_link.find_parent(['div', 'article'])

                    if article_container:
                        # Buscar el título (generalmente es el primer enlace con la clase article-title o similar)
                        title = None
                        title_elem = article_container.find(['h2', 'h3', 'a'])
                        if title_elem:
                            title = title_elem.text.strip()

                        # Buscar el DOI
                        doi = None
                        doi_pattern = r'10\.22514/jofph\.\d{4}\.\d{3}'
                        doi_match = re.search(doi_pattern, str(article_container))
                        if doi_match:
                            doi = doi_match.group(0)

                        # Obtener el link del PDF
                        pdf_url = pdf_link['href']

                        # Extraer volumen e issue de la URL original
                        url_parts = url.split('/')[-1].split('-')
                        volume = int(url_parts[0].replace('articles/', ''))
                        issue = int(url_parts[1]) if len(url_parts) > 1 else 1

                        article_info = {
                            'title': title,
                            'doi': doi,
                            'pdf_url': pdf_url,
                            'volume': volume,
                            'issue': issue
                        }

                        articles.append(article_info)
                        st.write(f"Artículo encontrado: {title}")
                        st.write(f"PDF URL: {pdf_url}")

                except Exception as e:
                    st.write(f"Error procesando artículo individual: {str(e)}")
                    continue

            st.write(f"Total artículos encontrados: {len(articles)}")
            return articles

        except Exception as e:
            st.error(f"Error en get_articles_from_url: {str(e)}")
            raise

    def download_pdf(self, pdf_url, filepath):
        try:
            response = self.session.get(pdf_url, headers=self.headers, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            st.error(f"Error descargando PDF: {str(e)}")
            return False