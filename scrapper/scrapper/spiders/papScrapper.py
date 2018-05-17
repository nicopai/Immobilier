import scrapy
import json
import re
import dateparser
from ..items import AnnoncePapItem
import os
import datetime as dt


class PapSpider(scrapy.Spider):
    name = "pap"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._annonces_parse = []
        self.charger_annonce_parse()
        self.nb_pages = 0
        self.startTimeStr = dt.datetime.now().strftime('%Y%m%d.%H%M%S')
        self.nb_already_parsed = 0
        if not os.path.exists('scrappeddocuments'):
            os.mkdir('scrappeddocuments')

    def charger_annonce_parse(self):
        if not os.path.exists('annonce.csv'):
            return
        f = open('annonce.csv', 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            split_line = line.split(',')
            self._annonces_parse.append((split_line[0], split_line[1].strip('\n')))

    def sauver_annonce_parse(self):
        write_lines = ['{},{}\n'.format(line[0], line[1]) for line in self._annonces_parse]
        f = open('annonce.csv','w+')
        f.writelines(write_lines)
        f.close()

    def start_requests(self):
        urls = [
            'https://www.pap.fr/annonce/locations-appartement-paris-75-g439-du-studio-au-3-pieces',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def save_page(self, response, filename):
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.logger.info('Saved file %s' % filename)

    def parse(self, response):
        filename = '{}.MainPage.{:d}.html'.format(self.startTimeStr, self.nb_pages)
        filepath = os.path.join('scrappeddocuments', filename)
        self.save_page(response,filepath)
        annonce_deja_parse = False
        for item in response.css('div.search-list-item'):
            annonce_id = item.css('div.item-content div.infos-box::attr(data-annonce)').re_first('\d+')

            last_update_str = response.css('p.item-date::text').extract_first()
            date_pattern = re.compile('/[^/]*$')
            last_update = dateparser.parse(date_pattern.findall(last_update_str)[0]).date().strftime('%y%m%d')

            annonce_id_date = (annonce_id, last_update)
            annonce_deja_parse = (annonce_id_date in self._annonces_parse)

            if annonce_deja_parse:
                self.nb_already_parsed += 1
                self.logger.debug('{} is already parsed'.format(annonce_id_date))
            else:
                self.logger.debug('Parsing {}'.format(annonce_id_date))
                self.nb_already_parsed = 0
                self._annonces_parse.append(annonce_id_date)
                lien_annonce = item.css('div.item-content a.item-title::attr(href)').extract_first()
                req = response.follow(lien_annonce, self.parse_annonce)
                print('{}'.format(annonce_id))
                req.meta['annonce_id'] = annonce_id
                yield req

        self.sauver_annonce_parse()
        self.nb_pages += 1
        next_page = response.css('li.next a::attr(href)').extract_first()
        if next_page and self.nb_already_parsed < 3 and self.nb_pages < 30:
            req = response.follow(next_page, self.parse)
            yield req

    def parse_annonce(self, response):
        item = AnnoncePapItem()
        lien = response.url
        annonce_id = response.meta['annonce_id']
        filename = '{}.MainPage.{:d}.Annonce.{}.html'.format(self.startTimeStr, self.nb_pages, annonce_id)
        filepath = os.path.join('scrappeddocuments',filename)
        self.save_page(response, filepath)
        item['lien'] = lien
        item['id'] = annonce_id
        col_2_3_info = response.css('div.col-2-3 strong::text').extract()
        piece_pattern = re.compile('.*pièce')
        chambre_pattern = re.compile('.*chambre')
        surface_pattern = re.compile('.*m²')
        number_pattern = re.compile('\d+')
        nb_pieces = 0
        nb_chambres = 0
        surface_m2 = 0
        for info in col_2_3_info:
            if piece_pattern.match(info):
                number = number_pattern.findall(info)[0]
                nb_pieces = int(number)
            if chambre_pattern.match(info):
                number = number_pattern.findall(info)[0]
                nb_chambres = int(number)
            if surface_pattern.match(info):
                number = number_pattern.findall(info)[0]
                surface_m2 = int(number)
        item['nb_pieces'] = nb_pieces
        item['nb_chambres'] = nb_chambres
        item['surface_m2'] = surface_m2

        price_str = response.css('span.item-price::text').extract_first().replace('.','')
        item['price'] = float(number_pattern.findall(price_str)[0])

        title_str  = response.css('span.h1::text').extract_first()
        item['title'] = title_str
        description_str = response.css('div.margin-bottom-30 p::text').extract()

        trimmedArray = [line.strip() for line in description_str]
        trimmedArray = [line for line in trimmedArray if line]
        item['description']='\n'.join(trimmedArray)

        coordonnees_str = response.css('div::attr(data-mappy)').extract_first()
        item['coordonnes'] = json.loads(coordonnees_str)['center']
        precision_adresse = response.css('div.item-description a::text').extract_first()
        adress_pattern = re.compile('adresse')
        precision_adresse = bool(adress_pattern.match(precision_adresse))
        item['precision_adresse'] = precision_adresse

        last_update_str = response.css('p.item-date::text').extract_first()
        date_pattern = re.compile('/[^/]*$')
        item['last_update'] = dateparser.parse(date_pattern.findall(last_update_str)[0]).date().strftime('%y%m%d')
        return item


