#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging, logging.handlers
import os
from configparser import ConfigParser
from datetime import datetime
from random import choice, random, seed
from time import sleep

import requests
from PyRSS2Gen import RSS2, Guid, RSSItem


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_USER, address='/dev/log')
formatter = logging.Formatter('%(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


user_agents = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
)

limit = 35

def scrape_offers(search_parameters):

    search_parameters['limit'] = limit
    search_parameters['offset'] = 0
    try:
        page = sess.post('https://api.leboncoin.fr/finder/search', json=search_parameters, timeout=5)
        sleep(10*random())
    except requests.exceptions.Timeout:
        logger.info('Timeout # first page')
        #logger.exception(e)
        return []

    data = json.loads(page.text)

    offers = []
    offers.extend(extract_offers(data))

    if data['total'] <= limit:
        return data['total'], offers
    else:
        errors = 0
        for offset in range(limit, data['total'], limit):
            search_parameters['offset'] = offset

            try:
                page = sess.post('https://api.leboncoin.fr/finder/search', json=search_parameters, timeout=5)
                offers.extend(extract_offers(json.loads(page.text)))
                sleep(10*random())
            except requests.exceptions.Timeout:
                errors += 1
                sleep(10*random())
                logger.info("Timeout %d # %s" % (errors, offset))

        return data['total'], offers


def extract_offers(json_data):
    items = []
    for o in json_data['ads']:
        # id_offer = o['list_id']
        article = {
            'title': o['subject'],
            'link': o['url'],
            'description': o['body'].strip(),
            'guid': Guid(o['url']),
            'pubDate': datetime.strptime(o['first_publication_date'], '%Y-%m-%d %H:%M:%S'),
        }

        if o['price']:
            prix = "Prix : {} €\n".format(o['price'][0])
        else:
            prix = ''
        adresse = "Adresse : {}\n".format(o['location']['city_label'])
        article['description'] = prix + adresse + "\n" + article['description']

        if o['images']['nb_images'] > 0:
            img = '<img src="{}" align="right" referrerpolicy="no-referrer" />'.format(o['images']['small_url'])
        else:
            img = ''
        article['description'] = "{}<pre>{}</pre>".format(img, article['description'])

        items.append(article)

    return items


if __name__ == '__main__':

    seed()

    config = ConfigParser(interpolation=None)
    config.read("lbc.conf")
    my_searchs = []
    ovhServer = False

    for s in config.sections():
        if s == 'Conf':
            RSS_root = config.get(s, 'Directory')
            URL_root = config.get(s, 'Url')
        elif s == 'Ovh':
            ovhServer = True
            ovhIp = config.get(s, 'Ip')
        else:
            File = s
            Name = str(config.get(s, 'Name'))
            Search = json.loads(config.get(s, 'Search'))
            my_searchs.append( (Name, Search, File, ) )

    logger.info("Démarrage...")
    sleep(3600*random())
    logger.info("Fin du sleep initial...")

    sess = requests.Session()
    sess.headers.update({
        'User-Agent': choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.8,en-GB;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
    })
    sess.get('https://www.leboncoin.fr/annonces/offres/rhone_alpes/')
    sess.headers.update({
        'api_key':'ba0c2dad52b3ec',
        'Referer': 'https://www.leboncoin.fr/annonces/offres/rhone_alpes/',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Origin': 'https://www.leboncoin.fr',
    })
    sleep(10*random())

    for title, search_parameters, filename in my_searchs:
        new, offers = scrape_offers(search_parameters)
        logger.info("%s : %d annonces" % (title, new))
        rss = RSS2(
            title = title, link = os.path.join(URL_root, filename), description = title, lastBuildDate = datetime.now(),
            items = [ RSSItem(**article) for article in offers ]
        )
        with open(os.path.join(RSS_root, filename), "w") as fic:
            rss.write_xml(fic, encoding='utf-8')
        sleep(30*random())

    logger.info("Fin...")

