from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Chrome ayarları
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Headless çalışmalı server ortamı için
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Tarayıcıyı başlat
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

def get_movie_music(film_adi, year):
    """Filmler için müzik listesi alır"""
    try:
        film_url = f"https://www.tunefind.com/movie/{film_adi.lower().replace(' ', '-')}-{year}"
        driver.get(film_url)
        return extract_music_data()
    except Exception as e:
        print(f"Film hatası: {str(e)}")
        return None

def get_show_music(show_name, season):
    """Diziler için sezon bazlı müzik listesi alır"""
    full_music_list = []
    show_url = f"https://www.tunefind.com/show/{show_name.lower().replace(' ', '-')}/season-{season}"
    driver.get(show_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-discover='true'][href^='/show/']"))
        )
    except TimeoutException:
        print("⚠️ Bölüm linkleri yüklenemedi.")
        return None

    episode_urls = [
        a.get_attribute("href")
        for a in driver.find_elements(By.CSS_SELECTOR, "a[data-discover='true'][href^='/show/']")
    ]

    for ep_url in episode_urls:
        driver.get(ep_url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-discover='true'][href^='/song/']"))
            )
        except TimeoutException:
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        song_links = soup.select("a[data-discover='true'][href^='/song/']")

        for song_a in song_links:
            title_tag = song_a.find("p")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            artist_a = song_a.find_next_sibling(
                "a",
                attrs={
                    "data-discover": "true",
                    "href": re.compile(r"^/artist/")
                }
            )
            artist = artist_a.find("small").get_text(strip=True) if artist_a else "Unknown"
            full_music_list.append((title, artist))

        time.sleep(0.5)

    return full_music_list if full_music_list else None

def extract_music_data():
    """Ortak müzik veri çekme fonksiyonu"""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-discover='true'][href^='/song/'] p"))
        )
        music_list = []
        for song in driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.gap-y-6, .SongRow"):
            try:
                title = song.find_element(
                    By.CSS_SELECTOR, 
                    "a[data-discover='true'][href^='/song/'] p"
                ).text.strip()

                artist = song.find_element(
                    By.CSS_SELECTOR, 
                    "a[data-discover='true'][href^='/artist/'] small"
                ).text.strip()

                music_list.append((title, artist))
            except NoSuchElementException:
                continue

        return music_list if music_list else None
    except TimeoutException:
        return None

# Opsiyonel: script sonlandığında browser kapatılabilir
import atexit
atexit.register(driver.quit)
