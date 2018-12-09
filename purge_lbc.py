#!/usr/bin/env python
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

    conn.commit()
    curs.execute("VACUUM;")
    conn.close()

