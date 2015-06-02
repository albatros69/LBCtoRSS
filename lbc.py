#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, sqlite3, re, os
from datetime import datetime
from time import sleep
from lxml.html import fromstring
from lxml.etree import tostring
from PyRSS2Gen import RSS2, RSSItem, Guid
from ConfigParser import ConfigParser

def extract_offers(url):
    try:
        if isinstance(url, requests.Response):
            tree = fromstring(url.text)
        else:
            page = requests.get(url, timeout=2)
            tree = fromstring(page.text)
    except:
        return []
    else:
        return tree.xpath('//div[@class="list-lbc"]/a/@href')


re_id = re.compile('.*/(?P<id>[0-9]+)\.htm.*')
conn = sqlite3.connect('lbc.sqlite')
curs = conn.cursor()

conn.execute('CREATE TABLE IF NOT EXISTS offers_seen (id INTEGER PRIMARY KEY, title TEXT, link TEXT, description TEXT, date TEXT default CURRENT_TIMESTAMP)')


def scrape_url(url):
    if ovhServer:
        url = url.replace("www.leboncoin.fr", ovhIp)
    main_page = requests.get(url, timeout=2)
    tree = fromstring(main_page.text)

    offers = []
    offers.extend(extract_offers(main_page))

    # Handling of next pages via paging links
    already_seen = []
    next_pages = list(tree.xpath('//ul[@id="paging"]//a/@href'))
    errors = 0
    while next_pages and errors <= 10:
        u = next_pages.pop(0)
        if ovhServer:
            u = u.replace("www.leboncoin.fr", ovhIp)
        if u in already_seen: continue

        try:
            offers.extend(extract_offers(u))
        except requests.exceptions.Timeout:
            errors += 1
            sleep(2)
            next_pages.append(u)
        else:
            already_seen.append(u)

    return offers


def scrape_offers(offer_urls):

    items = []
    for o in offer_urls:
        m = re_id.match(o)
        if ovhServer:
            o = o.replace("www.leboncoin.fr", ovhIp)
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
                    page = requests.get(o, timeout=2)
                except requests.exceptions.Timeout:
                    # Pour récupérer l'annonce à la prochaine exécution
                    curs.execute('DELETE FROM offers_seen WHERE id=?;', (id_offer, ))
                    sleep(2)
                    continue

                if page.status_code != 200:
                    curs.execute('DELETE FROM offers_seen WHERE id=?;', (id_offer, ))
                    continue

                tree = fromstring(page.text)
                for n in tree.xpath('//div[@class="lbcContainer"]//*'):
                    if (n.tag == 'h1' or n.tag == 'h2') and 'id' in n.attrib and n.attrib['id'] == 'ad_subject':
                        article['title'] = unicode(n.text.strip())
                    elif n.tag == 'div' and 'class' in n.attrib and n.attrib['class'] == 'AdviewContent':
                        in_descr = True
                    elif n.tag == 'th' and n.text:
                        article['description'] += u"\n" + unicode(n.text.strip()) + ' '
                    elif (n.tag == 'td' and n.text) or \
                         (n.tag == 'span' and 'class' in n.attrib and n.attrib['class'] == 'price'):
                        article['description'] += unicode(n.text.strip())
                    elif n.tag == 'div' and 'class' in n.attrib and n.attrib['class'] == 'content':
                        article['description'] += u"\n\n" + unicode(n.text.strip())
                    elif in_descr and n.tag == 'br' and n.tail:
                        article['description'] += u"\n" + unicode(n.tail.strip())
                    elif not img and n.tag == 'div' and 'class' in n.attrib and n.attrib['class'] == 'print-image1':
                        child = n.find('img')
                        child.attrib['align'] = 'right'
                        img = tostring(child, method='html')

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
    return items


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

    for title, url, filename in my_searchs:
        offers = scrape_url(url)
        rss = RSS2(
            title = title.encode('utf-8'), link = os.path.join(URL_root, filename), description = title.encode('utf-8'), lastBuildDate = datetime.now(),
            items = [ RSSItem(**article) for article in scrape_offers(offers) ]
        )
        rss.write_xml(open(os.path.join(RSS_root, filename), "w"), encoding='utf-8')

    conn.commit()
    conn.close()
