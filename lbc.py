#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, sqlite3, re, os
from random import random, choice
from datetime import datetime
from time import sleep
from lxml.html import fromstring
from lxml.etree import tostring
from PyRSS2Gen import RSS2, RSSItem, Guid
from ConfigParser import ConfigParser
import logging, logging.handlers


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
def req_headers():
    return { 'User-Agent': choice(user_agents) }


def extract_offers(url):
    try:
        if isinstance(url, requests.Response):
            tree = fromstring(url.text)
        else:
            sleep(2*random())
            page = requests.get(url, headers=req_headers(), timeout=2)
            tree = fromstring(page.text)
    except Exception as e:
        #logger.info(url)
        #logger.exception(e)
        #return []
        raise
    else:
        return tree.xpath('//section[contains(@class, "tabsContent")]//a[contains(@class, "list_item")]/@href')


re_id = re.compile('.*/(?P<id>[0-9]+)\.htm.*')
conn = sqlite3.connect('lbc.sqlite')
curs = conn.cursor()

conn.execute('CREATE TABLE IF NOT EXISTS offers_seen (id INTEGER PRIMARY KEY, title TEXT, link TEXT, description TEXT, date TEXT default CURRENT_TIMESTAMP)')


def scrape_url(url):
    if ovhServer:
        url = url.replace("www.leboncoin.fr", ovhIp)
    try:
        main_page = requests.get(url, headers=req_headers(), timeout=5)
    except Exception as e:
        logger.info('Timeout ### %s' % (url,) )
        #logger.exception(e)
        return []

    tree = fromstring(main_page.text)

    offers = []
    offers.extend(extract_offers(main_page))

    # Handling of next pages via paging links
    already_seen = []
    next_pages = list(tree.xpath('//div[contains(@class, "pagination_links_container")]//a/@href'))
    errors = 0
    while next_pages and errors <= 10:
        u = next_pages.pop(0)
        if ovhServer:
            u = u.replace("www.leboncoin.fr", ovhIp)
        if not u.startswith('http'):
            u = 'https:' + u
        if u in already_seen: continue

        try:
            offers.extend(extract_offers(u))
        except requests.exceptions.Timeout:
            errors += 1
            sleep(2*random())
            logger.info("Timeout %d ### %s" % (errors, u))
            next_pages.append(u)
        else:
            already_seen.append(u)

    return offers


def scrape_offers(offer_urls):

    items = []
    new_offers = 0
    for o in offer_urls:
        m = re_id.match(o)
        if ovhServer:
            o = o.replace("www.leboncoin.fr", ovhIp)
        if not o.startswith('http'):
            o = 'https:' + o
        if not m:
            continue
        else:
            id_offer = m.group('id')
            article = { 'title': '', 'link': o, 'description': '', 'guid': Guid(o), 'pubDate': datetime.now(), }
            img = ''
            in_descr = False

            curs.execute('INSERT OR IGNORE INTO offers_seen (id) VALUES (?);', (id_offer, ))
            if curs.rowcount > 0:
                try:
                    page = requests.get(o, headers=req_headers(), timeout=5)
                except requests.exceptions.Timeout:
                    # Pour récupérer l'annonce à la prochaine exécution
                    curs.execute('DELETE FROM offers_seen WHERE id=?;', (id_offer, ))
                    logger.info('Timeout offer ### %s' % (o, ))
                    sleep(2*random())
                    continue

                if page.status_code != 200:
                    curs.execute('DELETE FROM offers_seen WHERE id=?;', (id_offer, ))
                    continue

                new_offers += 1

                tree = fromstring(page.text)
                for n in tree.xpath('//section[@id="adview"]//*'):
                    if (n.tag == 'h1' or n.tag == 'h2') and 'class' in n.attrib and 'no-border' in n.attrib['class']:
                        article['title'] = unicode(n.text.strip())
                    elif n.tag == 'p' and 'id' in n.attrib and n.attrib['id'] == 'description':
                        in_descr = True
                        article['description'] += u"\n\n" + unicode(n.text.strip())
                    elif n.tag == 'p' and 'itemprop' in n.attrib and n.attrib['itemprop'] == 'description':
                        in_descr = True
                        article['description'] += u"\n\n" + unicode(n.text.strip())
                    elif in_descr and n.tag == 'br' and n.tail:
                        article['description'] += u"\n" + unicode(n.tail.strip())
                    elif n.tag == 'p' and 'id' in n.attrib and n.attrib['id'] == 'description_truncated':
                        in_descr = False
                    elif n.tag == 'h2' and 'itemprop' in n.attrib and n.attrib['itemprop'] == 'price':
                        article['description'] += u"Prix : " + unicode(n.attrib['content'].strip()) + u"€"
                    elif n.tag == 'span' and 'itemprop' in n.attrib and n.attrib['itemprop'] == 'address':
                        article['description'] += u"\nAdresse : " + unicode(n.text.strip())
                    elif not img and n.tag == 'div' and 'class' in n.attrib and 'item_image' in n.attrib['class'] \
                        and 'data-popin-content' in n.attrib:
                        img = '<img src="%s" align="right" />' % n.attrib['data-popin-content'].replace('large', 'image')

                if article['description'] and img:
                    article['description'] = "%s<pre>%s</pre>" % (img.strip(), article['description'].strip(), )
                elif article['description']:
                    article['description'] = "<pre>%s</pre>" % (article['description'].strip(), )

                if ovhServer:
                    article['link'] = article['link'].replace(ovhIp, "www.leboncoin.fr")

                curs.execute('UPDATE offers_seen SET title = ?, link = ?, description = ? WHERE id = ?;',
                    (article['title'], article['link'], article['description'], id_offer) )
            else:
                curs.execute('SELECT title, description, date FROM offers_seen WHERE id = ?;', (id_offer, ))
                for title, description, date in curs:
                    article['title'] = title
                    #article['link'] = o
                    article['description'] = description
                    #article['guid'] = Guid(o)
                    article['pubDate'] = datetime.strptime(date.decode('utf-8'), '%Y-%m-%d %H:%M:%S')

            items.append(article)

    conn.commit()
    return new_offers, items


if __name__ == '__main__':

    config = ConfigParser()
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
            Name = config.get(s, 'Name').decode('utf-8')
            Link = config.get(s, 'Link')
            my_searchs.append( (Name, Link, File, ) )

    logger.info("Démarrage...")
    for title, url, filename in my_searchs:
        new, offers = scrape_offers(scrape_url(url))
        logger.info("%s : %d nouvelle(s) annonce(s)" % (title, new))
        rss = RSS2(
            title = title.encode('utf-8'), link = os.path.join(URL_root, filename), description = title.encode('utf-8'), lastBuildDate = datetime.now(),
            items = [ RSSItem(**article) for article in offers ]
        )
        rss.write_xml(open(os.path.join(RSS_root, filename), "w"), encoding='utf-8')

    conn.commit()
    conn.close()
    logger.info("Fin...")

