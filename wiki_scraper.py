import argparse
import json
import os
import re
import time
from collections import Counter
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from wordfreq import word_frequency, top_n_list


class WikiScraper:
    def __init__(self, base_url, phrase, html_file=None):
        self.base_url = base_url
        self.phrase = phrase
        self.html_file = html_file

    def _get_soup(self):
        # jeśli mamy plik, to otwieramy i zwracamy uporządkowany
        if self.html_file:
            try:
                with open(self.html_file, "r", encoding="utf-8") as f:
                    text = f.read()
                return BeautifulSoup(text, "html.parser")
            except FileNotFoundError:
                print(f"Nie znaleziono pliku {self.html_file}")
                return None

        # zamieniamy spacje na _ i tworzymy url
        phrase = self.phrase.replace(" ", "_")
        url = self.base_url + phrase

        # pobieramy
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Nie udało się pobrać {url}")
            return None

        return BeautifulSoup(response.text, "html.parser")

    def get_summary(self):
        soup = self._get_soup()
        if not soup:
            print("Błąd! Artykuł nie istnieje lub błąd pobierania")
            return None

        # mw-content-text - ID dla treści w silnikach MediaWiki
        content_div = soup.find("div", id="mw-content-text")
        if not content_div:
            print("Błąd, brak sekcji treści na stronie")
            return None

        first_paragraph = content_div.find("p")
        if first_paragraph:
            text = first_paragraph.get_text().strip()
            print(text)
            return text
        else:
            print("Nie znaleziono paragrafu w artykule")
            return None

    def get_table(self, table_number, first_row_is_header):
        soup = self._get_soup()
        if not soup:
            print("Błąd! Artykuł nie istnieje lub błąd pobierania")
            return None

        try:
            dfs = pd.read_html(StringIO(str(soup)))
        except ValueError:
            print("Brak tabel na stronie")
            return None

        if table_number < 1 or table_number > len(dfs):
            print(f"Błąd, nie ma tabeli {table_number}.")
            return None

        df = dfs[table_number - 1]

        if first_row_is_header:
            new_header = df.iloc[0]
            df = df.iloc[1:]
            df.columns = new_header

        phrase = re.sub(r"\W+", "_", self.phrase)
        filename = f"{phrase}.csv"

        df.to_csv(filename, index=False, encoding="utf-8")

        print("\n--- STATYSTYKI TABELI ---\n")
        for column in df.columns:
            print("-" * 30)
            print(df[column].value_counts().to_string())

        return df

    def count_words(self):
        soup = self._get_soup()
        if not soup:
            print("Błąd! Artykuł nie istnieje lub błąd pobierania")
            return None

        # mw-content-text - ID dla treści w silnikach MediaWiki
        content_div = soup.find("div", id="mw-content-text")
        if not content_div:
            print("Błąd, brak sekcji treści na stronie")
            return None

        text = content_div.get_text()
        words = re.findall(r"\w+", text)

        counted_words_now = Counter(words)

        filename = "word-counts.json"

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                total_number_of_words = json.load(f)
                total_number_of_words = Counter(total_number_of_words)
        else:
            total_number_of_words = Counter()

        total_number_of_words.update(counted_words_now)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(total_number_of_words, f, ensure_ascii=False, indent=4)
        return dict(total_number_of_words)

    def auto_count_words(self, depth, wait_time):
        visited = set()
        queue = [(self.phrase, 0)]

        while queue:
            phrase, level = queue.pop(0)
            if phrase in visited:
                continue

            visited.add(phrase)

            # dla każdego linku oddzielny scraper, żeby nie zmieniać początkowego obiektu
            if phrase == self.phrase:
                worker = self
            else:
                worker = WikiScraper(self.base_url, phrase)

            print(f"Przetwarzana fraza: {phrase}")
            worker.count_words()

            if level < depth:
                soup = worker._get_soup()
                if not soup:
                    print("Błąd! Artykuł nie istnieje lub błąd pobierania")
                    continue

                # tylko z content div, żeby nie łapało linków z menu
                content_div = soup.find("div", id="mw-content-text")
                if not content_div:
                    print(f"Brak treści na stronie {phrase}")
                links = content_div.find_all("a", href=True)

                for link in links:
                    href = link["href"]
                    if href.startswith("/wiki/") and ":" not in href:
                        new_phrase = href.replace("/wiki/", "")
                        if new_phrase not in visited:
                            queue.append((new_phrase, level + 1))

                time.sleep(wait_time)
        return None


class WikiScraperController:
    def __init__(self, args):
        self.args = args
        self.phrase = self._get_phrase()
        html_file = getattr(args, "html_file", None)
        self.scraper = (
            WikiScraper(
                base_url="https://bulbapedia.bulbagarden.net/wiki/",
                phrase=self.phrase,
                html_file=html_file,
            )
            if self.phrase
            else None
        )

    def _get_phrase(self):
        if self.args.summary:
            return self.args.summary
        if self.args.table:
            return self.args.table
        if self.args.count_words:
            return self.args.count_words
        if self.args.auto_count_words:
            return self.args.auto_count_words
        return None

    def run(self):
        if self.args.analyze_relative_word_frequency:
            count = getattr(self.args, "count", 10)
            mode = getattr(self.args, "mode", "article")
            chart = getattr(self.args, "chart", False)
            analyze_relative_word_frequency(count, mode, chart)
            return

        if not self.scraper:
            print("Brak frazy do przetworzenia.")
            return

        if self.args.summary:
            self.scraper.get_summary()

        if self.args.table:
            number = getattr(self.args, "number", 1)
            first_row_is_header = getattr(self.args, "first_row_is_header", False)

            if number < 1:
                print("Numer tabeli musi być >= 1, był <1. Ustawiono 1.")
                number = 1

            self.scraper.get_table(number, first_row_is_header)

        if self.args.count_words:
            self.scraper.count_words()

        if self.args.auto_count_words:
            depth = getattr(self.args, "depth", 1)
            wait = getattr(self.args, "wait", 1)

            if wait < 1:
                print(f"Za niski czas oczekiwania - {wait}s. Zmieniono na 1 sekundę.")
                wait = 1

            self.scraper.auto_count_words(depth, wait)


def analyze_relative_word_frequency(n, mode, chart=None):
    filename = "word-counts.json"
    if not os.path.exists(filename):
        print(f"Plik {filename} nie istnieje. Uruchom najpierw --count-words")
        return

    with open(filename, "r", encoding="utf-8") as f:
        word_counts = json.load(f)

    df_word_counts = pd.DataFrame(word_counts.items(), columns=["word", "count"])
    df_word_counts["word"] = df_word_counts["word"].str.lower()
    df_word_counts = df_word_counts.groupby("word")["count"].sum()

    if mode == "article":
        n_most_used_words = df_word_counts.nlargest(n).index.tolist()
    else:  # mode == 'language'
        n_most_used_words = top_n_list("en", n)

    df = pd.DataFrame({"word": n_most_used_words})

    df["wiki"] = df["word"].map(df_word_counts).fillna(0)
    df["lang"] = df["word"].apply(lambda w: word_frequency(w, "en"))

    wiki_max = df_word_counts.max() if not df_word_counts.empty else 1
    lang_max = word_frequency("the", "en")

    df["freq_article"] = df["wiki"] / wiki_max
    df["freq_lang"] = df["lang"] / lang_max

    output = df[["word", "freq_article", "freq_lang"]].copy()
    output.columns = ["Word", "Frequency in Article", "Frequency in Language"]
    print(output.to_string(index=False, float_format="%.4f"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Narzędzie do scrapowania i analizy danych z Wiki."
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--summary", type=str, help="summary")
    group.add_argument("--table", type=str, help="table")
    group.add_argument("--count-words", type=str, help="count words")
    group.add_argument("--auto-count-words", type=str, help="")
    group.add_argument(
        "--analyze-relative-word-frequency", action="store_true", help=""
    )

    # do table
    parser.add_argument("--number", type=int, default=1, help="numer do tabeli")
    parser.add_argument(
        "--first-row-is-header",
        action="store_true",
        help="czy nagłówek pierwszy w tabeli",
    )

    # do analyze
    parser.add_argument(
        "--mode", type=str, default="article", choices=["article", "language"], help=""
    )
    parser.add_argument("--count", type=int, default=10, help="Liczba wierszy")
    parser.add_argument("--chart", type=str, help="")

    # do auto-count
    parser.add_argument("--depth", type=int, default=1, help="")
    parser.add_argument("--wait", type=float, default=1, help="")

    parser.add_argument("--html-file", type=str, help="link do pliku na dysku")

    args = parser.parse_args()

    app = WikiScraperController(args)
    app.run()
