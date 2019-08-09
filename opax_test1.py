#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This is script to monitor opax accounts
"""

__author__ = "Georg Wallisch"
__contact__ = "gw@phpco.de"
__copyright__ = "Copyright © 2019 by Georg Wallisch"
__credits__ = ["Georg Wallisch"]
__date__ = "2019/04/14"
__deprecated__ = False
__email__ =  "gw@phpco.de"
__license__ = "open source software"
__maintainer__ = "Georg Wallisch"
__status__ = "alpha"
__version__ = "0.1"

import ConfigParser
import requests
import re
import os
import io
import sys
import HTMLParser
from datetime import datetime
#import time


def get_opaxpage(accdata):
	payload = {'LANG': 'de', 'FUNC': 'medk', 'BENUTZER': accdata["userid"], 'PASSWORD': accdata["passwd"]}
	r = requests.post("{}/user.C".format(accdata["url"]), data=payload)
	return r.text

def main():
	global accountconfig, args, basepath
	accountconfig = []
	basepath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
	
	try:		
		with open(os.path.join(basepath,"opax.cfg")) as f:
			opax_config = f.read()
		config = ConfigParser.RawConfigParser()
		config.readfp(io.BytesIO(opax_config))
		
		for i in range(1,9):
			a = "account{}".format(i)
			if config.has_section(a):
				nm = config.get(a,'name')
				us = config.get(a,'userid')
				pw = config.get(a,'passwd')
				mail = config.get(a,'mail')
				url = config.get(a,'opaxurl')
				accountconfig.append({'name':nm, 'userid':us, 'passwd':pw, 'mail':mail, 'url':url})
		
	except ConfigParser.NoSectionError:
		print("Konfigurationsabschnitt fehlt!\n")
	except ConfigParser.ParsingError:
		print("Fehlerhafte Konfigurationsdatei!\n")
		raise
	except ConfigParser.Error:
		print("Allgemeiner Konfigurationsfehler!\n")
		raise
		
	try:	
		nixgeliehen = re.compile(r"Kein.*Medium.*ausgeliehen",flags=re.U|re.I|re.S)
		p = re.compile(r"<form[^>]*>.*<table[^>]*>(.*)</table>.*?</form>",flags=re.U|re.I|re.S)
		liste = re.compile(r"<tr[^>]*>.*?<td[^>]*>\s*(\d{2}\.\d{2}\.\d{4})\s*</td[^>]*>.*?<td[^>]*>\s*(\d{5,})\s*</td[^>]*>.*?<td[^>]*>\s*<a[^>]*>\s*([^<>]*)\s*</a[^>]*>\s*</td[^>]*>.*?</tr[^>]*>",flags=re.U|re.I|re.S)
		h = HTMLParser.HTMLParser()
		for acc in accountconfig:
			print("\n-----\nLese Account {}:\n".format(acc["name"]))
			html = get_opaxpage(acc)
			#print(type(html))
			x = nixgeliehen.search(html)
			if x:
				print("Kein Medium ausgeliehen!\n")
				#print(x.group(1))
			else:
				x = p.search(html)
				if x:
					#print(x.group(1))
					l = liste.findall(h.unescape(x.group(1)))
					if l:
						#print(l)
						heute = datetime.now()
						for ausgeliehen in l:
							#print(type(ausgeliehen))
							#print(ausgeliehen[0]," ",ausgeliehen[1]," ",ausgeliehen[2])
							faellig = datetime.strptime(ausgeliehen[0],  '%d.%m.%Y')
							diff = faellig - heute
							print(u"Fällig in {} Tagen: {} ({})".format(diff.days,ausgeliehen[2], ausgeliehen[1]))
							#for en in ausgeliehen:
							#	print(en)
					else:
						print("Warnung: Keine Liste gefunden!\n")
				else:
					print("Warnung: Unklares Ergebnis!")

	except KeyboardInterrupt:
		print("\nAbbruch durch Benutzer Ctrl+C")
	except RuntimeError as e:
		print("RuntimeError: ",e)
	except:
		print("Unexpected error: ", sys.exc_info()[0])
	finally:
		print("Finally ended")
		
if __name__ == "__main__":
	main()