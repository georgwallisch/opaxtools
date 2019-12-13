#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Georg Wallisch"
__contact__ = "gw@phpco.de"
__copyright__ = "Copyright © 2019 by Georg Wallisch"
__credits__ = ["Georg Wallisch"]
__date__ = "2019/12/14"
__deprecated__ = False
__email__ =  "gw@phpco.de"
__license__ = "open source software"
__maintainer__ = "Georg Wallisch"
__status__ = "alpha"
__version__ = "0.3"

import requests
import re
import HTMLParser
from datetime import datetime
from datetime import timedelta  
import logging

#reload(sys)
#sys.setdefaultencoding("utf-8")

class OpaxAccount:
	"""Query OPAx Host
	"""
	
	def __init__(self, userid, password, host, uri = 'opax/', protocol = 'https', verify_ssl = True, certificate=None, logger = None):
		if logger is None:
			console = logging.StreamHandler()
			self._log = logging.getLogger('OPAxAccount')
			self._log.addHandler(console)
		else:
			self._log = logger 
		
		self._log.info("Constructing new OPAx object")
		self.userid = userid
		self.password = password
		self.host = host
		self.uri = uri
		self.protocol = protocol
		self.verify_ssl = verify_ssl
		if certificate is not None:
			self.verify_ssl = certificate
		self.userpage = None
		self.lendings = None
		self.loaned = []
		self.accountvalidity_date = None
		self.accountvalidity_diff = None
			
	def get_opaxpage(self, page, payload):
		hosturl = "{}://{}/{}{}".format(self.protocol, self.host, self.uri, page)
		self._log.info("querying {}".format(hosturl))
		try:
			r = requests.post(hosturl, data=payload, verify=self.verify_ssl)
		except Exception as e:
			print("Request-Error: {0}".format(e))
			return None
		if r:
			return r.text.decode('UTF-8')
		else:
			return None
		
	def get_userinfo(self):
		self.userpage = self.get_opaxpage('user.C', {'LANG': 'de', 'FUNC': 'medk', 'BENUTZER': self.userid, 'PASSWORD': self.password})
			
	def get_titleinfo(self, title_id):
		t = self.get_opaxpage('ftitle.C', {'LANG': 'de', 'FUNC': 'full', 'DUM1': '0', title_id:'YES'})
		details = {}
		if t:
			self._log.info("Details zu Medium {} gefunden!".format(title_id))
			#p = re.compile(r"<table[^>]*>(.*)</table>", flags=re.U|re.I|re.S)
			#m = p.search(t)
			#if m:
			p = re.compile(r'<tr[^>]*>\s*<td[^>]*>\s*([^<>]+)\s*</td\s*>\s*<td[^>]*>\s*(.+?)\s*</td\s*>\s*</tr\s*>',flags=re.U|re.I|re.S)
			h = HTMLParser.HTMLParser()
			#l = p.findall(h.unescape(m.group(1)))
			l = p.findall(h.unescape(t))
			if l:
				self._log.debug(l)
				striptags = re.compile(r'</?[^>]+>',flags=re.U|re.I|re.S)
				for e in l:
					details[e[0].strip()] = striptags.sub('', e[1]).strip()
			else:
				self._log.info("Aber keine Regex Treffer!")
		return details 
		
	def parse(self):
		self.get_userinfo()
		h = HTMLParser.HTMLParser()
		heute = datetime.now()
		
		#self._log.debug(h.unescape(self.userpage))
		
		p = re.compile(r'Fehler in der Ausf.+hrung', flags=re.U|re.I|re.S)
		m = p.search(h.unescape(self.userpage))
		
		if m:
			self._log.info("Login fehlgeschlagen: 'Fehler in der Auführung'")
		else:
			p = re.compile(r'Ausweisg.+ltigkeit\:\s*(\d{2})\.(\d{2})\.(\d{4})', flags=re.U|re.I|re.S)
			m = p.search(h.unescape(self.userpage))
			
			if m: 
				self._log.info(m.group(0))
				self.accountvalidity_date = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), 23, 59, 59)
				self.accountvalidity_diff = self.accountvalidity_date - heute
			else:
				self._log.info(u"Keine Ausweisdaten gefunden!")
				
			p = re.compile(r'Kein.*Medium.*ausgeliehen', flags=re.U|re.I|re.S)
			m = p.search(self.userpage)
			
			if m:
				self._log.info(u"Kein Medium ausgeliehen!\n")
				self.lendings = 0			
			else:
				p = re.compile(r'<form[^>]*>.*<table[^>]*>(.*)</table>.*?</form>',flags=re.U|re.I|re.S)
				m = p.search(self.userpage)
				if m:
					p = re.compile(r'<tr[^>]*>.*?<td[^>]*>\s*(\d{2})\.(\d{2})\.(\d{4})\s*</td[^>]*>.*?<td[^>]*>\s*(\d{5,})\s*</td[^>]*>.*?<td[^>]*>\s*<a[^>]*"javascript:[^"]+?\'(\d+)\'[^"]*?"[^>]*>\s*([^<>]*)\s*</a[^>]*>\s*</td[^>]*>.*?</tr[^>]*>',flags=re.U|re.I|re.S)
					l = p.findall(h.unescape(m.group(1)))
					if l:
						self._log.info(u"Ausgeliehene Medien gefunden!\n")
						for e in l:
							self._log.info(e)
							faellig = datetime(int(e[2]), int(e[1]), int(e[0]), 23, 59, 59)
							diff = faellig - heute
							self._log.info(u"Faellig in {} Tagen: {} ({})".format(diff.days, e[5], e[3]))
							details = self.get_titleinfo(e[4])
							self.loaned.append({'deadline':faellig, 'diff':diff, 'shortname': e[5], 'id':e[3], 'details':details, 'detail_id':e[4]})
						self.lendings = len(self.loaned)
					else:
						self._log.warning(u"Trotz Tabelle keine Liste gefunden!\n")					
				else:
					self._log.warning(u"Unerwartetes Ergebnis!\n")	