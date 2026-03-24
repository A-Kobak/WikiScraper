import unittest
import os
from wiki_scraper import WikiScraper


class unitTests(unittest.TestCase):

    def setUp(self):
        self.test_file = "temp.html"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("<html></html>")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

        if os.path.exists("Test2.csv"):
            os.remove("Test2.csv")

    # W artykule nie ma paragrafu, summary powinno zwrócić None
    def test1_no_paragraph(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <div id="mw-content-text">
                <div>AAAAAAAAAAAAAABBBBBBBBBBBB</div>
                </li>
                    <li class="toclevel-1 tocsection-33"><a href="#In_the_TCG"><span class="tocnumber">6</span> <span class="toctext">In the TCG</span></a></li>
                    <li class="toclevel-1 tocsection-34"><a href="#Trivia"><span class="tocnumber">7</span> <span class="toctext">Trivia</span></a></li>
                    <li class="toclevel-1 tocsection-35"><a href="#Names"><span class="tocnumber">8</span> <span class="toctext">Names</span></a></li>
                </ul>
                <h2><span class="mw-headline" id="In_the_core_series_games">In the core series games</span></h2>
            </div>
        </body>
        </html>
        """
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        scraper = WikiScraper("http://mock", "Test1", html_file=self.test_file)

        result = scraper.get_summary()
        self.assertIsNone(result)

    # Test obsługi braku pliku HTML
    def test_missing_html_file(self):
        missing_file = "file_12345.html"

        scraper = WikiScraper("http://mock", "Test2", html_file=missing_file)
        result = scraper._get_soup()
        self.assertIsNone(result)

    # Tworzymy tabelę i sprawdzamy działanie flagi --first-row-is-header
    def test_table_header_logic(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <table>
                <tr><td>KolumnaA</td><td>KolumnaB</td></tr>
                <tr><td>Wartosc1</td><td>Wartosc2</td></tr>
            </table>
        </div>
        </body>
        </html>
        """
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        scraper = WikiScraper("http://mock", "Test3", html_file=self.test_file)

        df = scraper.get_table(1, first_row_is_header=True)

        self.assertIsNotNone(df)
        self.assertIn("KolumnaA", df.columns)
        self.assertIn("KolumnaB", df.columns)
        self.assertEqual(df.iloc[0]["KolumnaA"], "Wartosc1")

    # Sprawdzenie, czy konstruktor klasy WikiScraper poprawnie
    # przypisuje wartości do pól self.base_url, self.phrase oraz self.html_file
    def test_scraper_initialization(self):
        base_url = "https://test.wiki/"
        phrase = "Test4"
        html_file = "local_file.html"

        scraper = WikiScraper(base_url, phrase, html_file=html_file)

        self.assertEqual(scraper.base_url, base_url)
        self.assertEqual(scraper.phrase, phrase)
        self.assertEqual(scraper.html_file, html_file)


if __name__ == "__main__":
    unittest.main()
