import sys
import os
import requests
from wiki_scraper import WikiScraper

FILENAME = "team_rocket.html"
URL = "https://bulbapedia.bulbagarden.net/wiki/Team_Rocket"


# pomocnicza funkcja sprawdza czy plik istnieje, jeżeli nie, to zostanie pobrany
def ensure_file_exists():
    if os.path.exists(FILENAME):
        return True

    print("Nie było pliku, pobieram")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        with open(FILENAME, "w", encoding="utf-8") as f:
            f.write(response.text)
        return True
    else:
        print(f"Błąd pobierania: Status {response.status_code}")
        return False


def test_summary_integration():
    if not ensure_file_exists():
        print("Brak pliku")
        return False

    scraper = WikiScraper(
        base_url="https://bulbapedia.bulbagarden.net/wiki/",
        phrase="Team Rocket",
        html_file=FILENAME,
    )

    summary = scraper.get_summary()

    if not summary:
        print("get_summary zwróciło pusty wynik.")
        return False

    expected_start = "Team Rocket"
    expected_end_fragment = "outpost in the Sevii Islands."

    check_start = summary.startswith(expected_start)
    check_end = summary.endswith(expected_end_fragment)

    if not check_start:
        print(f"BŁĄD: Tekst nie zaczyna się od '{expected_start}'.")
        print(f"Początek: '{summary[:50]}...'")

    if not check_end:
        print(f"BŁĄD: Tekst nie kończy się na '{expected_end_fragment}'.")
        print(f"Koniec: '...{summary[-50:]}'")

    if check_start and check_end:
        print("SUKCES: Test integracyjny zaliczony.")
        return True
    else:
        return False


if __name__ == "__main__":
    success = test_summary_integration()

    sys.exit(0 if success else 1)
