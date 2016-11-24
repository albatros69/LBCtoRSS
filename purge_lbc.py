#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, sqlite3 #, re, os
from time import sleep
import logging, logging.handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_USER, address='/dev/log')
formatter = logging.Formatter('%(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

conn = sqlite3.connect('lbc.sqlite')
curs = conn.cursor()

if __name__ == '__main__':

    curs.execute("SELECT COUNT(*) FROM offers_seen;")
    logger.info( "%d annonces" % (curs.fetchone()[0], ))
    curs.execute("DELETE FROM offers_seen WHERE date < DATETIME('now', '-61 day');")
    logger.info("%d annonces de plus de 2 mois supprimées" % (curs.rowcount, ) )

    offers_deleted = []
    c = 0
    for i, u in curs.execute("SELECT id, link FROM offers_seen WHERE date < DATETIME('now', '-31 day');"):
        c += 1
        try:
            r = requests.head(u, timeout=2)
            #print i, u, r.status_code
        except:
            sleep(2)
            continue
        else:
            if r.status_code != 200:
                offers_deleted.append(str(i)) 
            sleep(0.5)

    curs.execute("DELETE FROM offers_seen WHERE id in (%s);" % (",".join(offers_deleted), ));
    logger.info("%d annonces introuvables supprimées parmi %d annonces de plus d'1 mois" % (len(offers_deleted), c) )
    curs.execute("VACUUM;")
    conn.commit()
    conn.close()

