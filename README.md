# Scraping NYC Treemap into Anki Deck

This is a project to create an Anki Deck to help learn the tree species in New York City.  The NYC Parks department generously maintains the [NYC Treemap
](https://tree-map.nycgovparks.org/), which is where we gather our data.

The simplest way to get going is to just import the existing deck into your Anki, but you can also create a deck from  the CSV with your own options, or run the script to get the data straight from the tap.

Enjoy!

### To import Anki Deck
```
Import file
Choose `NYC Trees.apkg`
```

### To load into Anki from CSV:
```
Copy all images from `images/` into Anki's Media folder (Anki > Tools > Check Media > View Files)
Import file
Choose tree_data.csv
Options:
Separate by comma
Allow HTML
```

### To scrape:
```
pipenv install
pipenv run python scrape_nyc_treemap.py
```
