import requests
import re
from abc import ABC, abstractmethod
from collections import namedtuple
from bs4 import BeautifulSoup
from typing import List, Callable


PhoneInfo = namedtuple("PhoneInfo", "manufacturer model_name model_code ram form_factor soc screen_sizes screen_densities ABIs android_sdk_versions opengl_es_versions")


class Price:
    def __init__(self, base_price: float, shipping: float = 0):
        self.base_price = base_price
        self.shipping = shipping

    def total(self) -> float:
        return self.base_price + self.shipping

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "%.2f + %.2f" % (self.base_price, self.shipping) if self.shipping > 0 else "%d" % (self.base_price,)


class Phone:
    def __init__(self, info: PhoneInfo, prices: List[Price]):
        self.info = info
        self.prices = prices

    def _fold(self, xs: List[Price], f: Callable[[List], float], default: float = 0) -> float:
        return (default if len(xs) == 0 else f([p.total() for p in xs]))

    @property
    def cheapest(self, normalised=True) -> float:
        return self._fold(self.remove_outliers() if normalised else self.prices, min)

    @property
    def most_expensive(self, normalised=True) -> float:
        return self._fold(self.remove_outliers() if normalised else self.prices, max)

    def remove_outliers(self, deviation: float = 0.5) -> List[Price]:
        if len(self.prices) == 0:
            return self.prices
        avg = sum([p.total() for p in self.prices]) / len(self.prices)
        return [p for p in self.prices if abs(avg - p.total()) < deviation * avg]

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "%s %s – %s" % (self.info.model_name, self.cheapest, self.most_expensive)


class PriceScraper(ABC):
    @abstractmethod
    def _url(self, info: PhoneInfo):
        pass

    @abstractmethod
    def _extract_prices(self, soup: BeautifulSoup):
        pass

    @abstractmethod
    def _extract_price(self, text) -> float:
        pass

    def lookup_price(self, info: PhoneInfo):
        print("Looking up price for '%s'" % (info.model_name,))
        r = requests.get(self._url(info))
        soup = BeautifulSoup(r.text, features="html5lib")
        prices = self._extract_prices(soup)
        phone = Phone(info, prices)
        print("Determined price range of %s – %s" % (phone.cheapest, phone.most_expensive))
        return phone


class GermanGoogleScraper(PriceScraper):
    def _url(self, info: PhoneInfo):
        return "https://www.google.com/search?q=%s&tbm=shop" % (info.model_name.replace(" ", "+"))

    def _extract_price(self, text) -> float:
        match = re.findall(r"(\d+(?:\.\d+)*)(?:,(\d+))?", text)
        if not match:
            raise Exception("no price found in '%s'" % (text,))
        number = "".join(re.findall(r"\d+", match[0][0]))
        decimal = match[0][1] if match[0][1] else "0"
        return float("%s.%s" % (number, decimal))

    def _extract_prices(self, soup: BeautifulSoup):
        price_tags = soup.body.findAll(text=re.compile(r"€"))  # match.find("Versandkosten") == -1]
        prices = []
        last: Price = None
        for pt in price_tags:
            if pt.startswith("+"):
                last.shipping = self._extract_price(pt)
            else:
                last = Price(base_price=self._extract_price(pt))
                prices.append(last)
        return prices


def read_infos(file):
    with open(file, "r") as fh:
        fh.readline()  # eliminate header
        return [PhoneInfo(*line.split(",")) for line in fh.read().split("\n")]


def write_prices(file, phones: List[Phone], separator=","):
    with open(file, "w") as fh:
        for p in phones:
            fh.write("%s%s%s%s%s\n" % (p.info.model_name, separator, p.cheapest, separator, p.most_expensive))


def main():
    infos = read_infos("arcore_devicelist_depth_api_support.csv")
    scraper = GermanGoogleScraper()
    phones = [scraper.lookup_price(p) for p in infos]
    write_prices("prices.csv", phones)


if __name__ == '__main__':
    main()
