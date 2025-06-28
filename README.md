# Scraping NYC Treemap into Anki Deck


To import Anki Deck
```
Import file
Choose `NYC Trees.apkg`
```

To load into Anki from CSV:
```
Copy all images from `images/` into Anki's Media folder (Anki > Tools > Check Media > View Files)
Import file
Choose tree_data.csv
Options:
Separate by comma
Allow HTML
```

To scrape:
```
pipenv install
pipenv run python scrape_nyc_treemap.py
```
