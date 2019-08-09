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
__version__ = "0.2"

import ConfigParser
import argparse
import os
import io
import sys
import logging
import opaxtools
from datetime import datetime
from datetime import timedelta  

#reload(sys)
#sys.setdefaultencoding("utf-8")


def main():
		
	try:
		argp = argparse.ArgumentParser(description=__doc__)
		argp.add_argument('--configfile', default=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'opax.cfg')),
				  help='Config file to use instead of standard opax.cfg')
		argp.add_argument('-v', '--verbose', action='count', default=0,
					  help='increase output verbosity (use up to 3 times)')
		args = argp.parse_args()
		
		if args.verbose > 1:
			logging.basicConfig(level=logging.DEBUG)
		elif args.verbose > 0:
			logging.basicConfig(level=logging.INFO)
			
			
		print(u"\n\n*** OPAx Test 2 ***\n\nBenutze Configfile: {}\n\n".format(args.configfile))
				
		with open(args.configfile) as f:
			opax_config = f.read()
		config = ConfigParser.RawConfigParser()
		config.readfp(io.BytesIO(opax_config))
		
		common_host = config.get('common','opax')
		common_mail = config.get('common','mail')
		
		accountconfig = []
		logging.info(u"Reading account configurations\n")
		
		for i in range(1,9):
			a = "account{}".format(i)
			if config.has_section(a):
				logging.info(u"Found config {}\n".format(i))
				nm = config.get(a,'name')
				us = config.get(a,'userid')
				pw = config.get(a,'passwd')
				accountconfig.append({'name':nm, 'userid':us, 'passwd':pw, 'mail':common_mail, 'host':common_host})
		
	except ConfigParser.NoSectionError:
		print("Konfigurationsabschnitt fehlt!\n")
	except ConfigParser.ParsingError:
		print("Fehlerhafte Konfigurationsdatei!\n")
		raise
	except ConfigParser.Error:
		print("Allgemeiner Konfigurationsfehler!\n")
		raise
		
	try:	
		logging.info(u"Iteration through all accounts\n")
		for acc in accountconfig:
			print(u"\n-----\nLese Account {}:\n".format(acc["name"]))
			logging.info(acc)
			o = opaxtools.OpaxAccount(acc['userid'], acc['passwd'], acc['host'])
			logging.info(u"Parsing OPAx data\n")
			o.parse()
			logging.info(u"Printing OPAx data\n")
			if o.accountvalidity_diff > timedelta(days=1):
				print(u"Account OK, noch {} Tage gültig (bis {})".format(o.accountvalidity_diff.days, o.accountvalidity_date.strftime('%d.%m.%Y')))
			elif o.accountvalidity_diff <= timedelta(days=1):
				print(u"PROBLEM: Account nur gültig bis {}!".format(o.accountvalidity_date.strftime('%d.%m.%Y')))
			else:
				print(u"Konnte Account-Gültigkeit nicht ermitteln!")
				
			if len(o.loaned) >  0:
				for medium in o.loaned:
					print(u"Fällig in {} Tagen ({}): {}".format(medium['diff'].days, medium['deadline'].strftime('%d.%m.%Y'), medium['shortname']))
					if medium['details']:
						print(u"\t{}: {}".format(medium['details']['Verfasser'], medium['details']['Titel']))
					#print(medium)
					
			else:
				print(u"Keine Medien ausgeliehen!")
				
			#print(o.loaned)

	except KeyboardInterrupt:
		print("\nAbbruch durch Benutzer Ctrl+C")
	except RuntimeError as e:
		print("RuntimeError: ",e)
	except Exception as e:
		    exc_type, exc_obj, exc_tb = sys.exc_info()
		    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		    print("Unexpected error: ",exc_type, fname, exc_tb.tb_lineno)
		#print( sys.exc_info()[0])
	finally:
		print("Finally ended")
		
if __name__ == "__main__":
	main()