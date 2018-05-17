# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class AnnoncePapItem(scrapy.Item):
    id = scrapy.Field()
    lien = scrapy.Field()
    nb_pieces = scrapy.Field()
    nb_chambres = scrapy.Field()
    surface_m2 = scrapy.Field()
    price = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    coordonnes = scrapy.Field()
    precision_adresse = scrapy.Field()
    last_update = scrapy.Field()
