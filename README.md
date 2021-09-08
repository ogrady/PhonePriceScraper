Small utility to look up price ranges for a list of phones.

# Purpose
For most use cases, websites like [idealo](https://www.idealo.co.uk/) will do the job more conveniently.
I was looking for an inexpensive phone that supports ARCore. No website I found supported this filter, so I was left with [a list of a few dozen phones](https://developers.google.com/ar/devices#google_play) to look up manually.

Instead, I wrote this little tool to scrape the _German_ Google shopping page for the price range and export it to a CSV file with the minimum and maximum prices that were found.

# Installation
Only dependency is BeautifulSoup:

```shell
pip install -r requirements.txt

```

# Running
From the root directory:
```shell
python scrapper.py

```