#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Georg Wallisch"
__contact__ = "gw@phpco.de"
__copyright__ = "Copyright © 2019 by Georg Wallisch"
__credits__ = ["Georg Wallisch"]
__date__ = "2019/12/14"
__deprecated__ = False
__email__ =	 "gw@phpco.de"
__license__ = "open source software"
__maintainer__ = "Georg Wallisch"
__status__ = "alpha"
__version__ = "0.3"


import nagiosplugin
import argparse
import requests
import io, os, sys
from datetime import datetime
from datetime import timedelta  
import logging
import opaxtools

#reload(sys)
#sys.setdefaultencoding("utf-8")

_log = logging.getLogger('nagiosplugin')



class OPAx(nagiosplugin.Resource, opaxtools.OpaxAccount):
	
	def __init__(self, userid, password, host, uri = 'opax/', protocol = 'https', verify_ssl = True, certificate=None):
		opaxtools.OpaxAccount.__init__(self, userid, password, host, uri, protocol, verify_ssl, certificate)	
	
	def probe(self):
		try:

			metrics = []
			self.parse()
			
			if self.accountvalidity_date is None:
				self._log.debug("No account data found!")
			else:
				self._log.debug("Account data found!")
				metrics.append(nagiosplugin.Metric(u'Account valid until {}'.format(self.accountvalidity_date.strftime("%Y-%m-%d")), self.accountvalidity_diff.days, context='accountvalidity', uom='d'))	
			
			if self.lendings is None:
				self._log.debug("No medium info found!")
			else:
				self._log.debug("Medium info found!")
				metrics.append(nagiosplugin.Metric(u'Medium(s) loaned', self.lendings, context='lendings'))		
				if self.lendings > 0:
					for medium in self.loaned:
						metrics.append(nagiosplugin.Metric(u'Return deadline of "{}" is {}'.format(medium['shortname'].encode('ascii','replace'), medium['deadline'].strftime('%d.%m.%Y')), medium['diff'].days, context='deadline', uom='d'))
					
		except requests.exceptions.SSLError as e:
			print("SSL-Verification of Host {0} failed!".format(self.host))
			print('Use `--verify-ssl=no` if you want to ignore.')
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print("Unexpected error: ",exc_type, fname, exc_tb.tb_lineno)
			
		finally:
			return metrics

@nagiosplugin.guarded
def main():
	argp = argparse.ArgumentParser(description=__doc__)
	argp.add_argument('-w', '--warning', metavar='RANGE', default='',
					  help='return warning if remaining days until deadline for returning is outside RANGE')
	argp.add_argument('-c', '--critical', metavar='RANGE', default='',
					  help='return critical if remaining days until deadline for returning is outside RANGE')
	argp.add_argument('--lendings', metavar='RANGE', default=',',
					  help='RANGE values warning,critical for count of loaned mediums')
	argp.add_argument('--validity', metavar='RANGE', default=',',
					  help='RANGE values warning,critical for account validity')	
	argp.add_argument('-H', '--host', required=True, help='OPAX Host')
	argp.add_argument('-p', '--protocol', default='https',
					  help='Protocol to access OPAX Host (default: https)')
	argp.add_argument('-u', '--uri', default='opax/',
					  help='OPAX URI on Host (default: opax/)')
	argp.add_argument('-U', '--userid', required=True,
					  help='User ID (Bibliotheksausweisnummer)')
	argp.add_argument('-P', '--password', required=True, 
					  help='Password (Normalerweise Geburtsdatum DDMMYYYY)')
	argp.add_argument('-v', '--verbose', action='count', default=0,
					  help='increase output verbosity (use up to 3 times)')
	argp.add_argument('-t', '--timeout', type=int, default=0,
					  help='timeout in seconds, default=0 (unlimited)')
	argp.add_argument("--debug", help="DEBUG Mode", action="store_true")
	argp.add_argument("--disable-ssl-verfication", help="Disable the security certificate check", action="store_true")
	argp.add_argument('--certificate', default=None, help='Path to specific cert to use')
	args = argp.parse_args()
	
	if args.debug:
		logging.basicConfig(level=logging.DEBUG)
	elif args.verbose > 2:
		logging.basicConfig(level=logging.INFO)
	elif args.verbose == 2:
		logging.basicConfig(level=logging.WARNING)
	elif args.verbose == 1:
		logging.basicConfig(level=logging.ERROR)
		
	w_lendings, c_lendings = args.lendings.split(',')
	w_validity, c_validity = args.validity.split(',')
	
	if args.disable_ssl_verfication:
		verify_ssl = False
	else:
		verify_ssl = True
	
	check = nagiosplugin.Check(
		OPAx(args.userid, args.password, args.host, args.uri, args.protocol,verify_ssl, args.certificate),
		nagiosplugin.ScalarContext('deadline', args.warning, args.critical, fmt_metric='{value} days left'),
		nagiosplugin.ScalarContext('lendings', w_lendings, c_lendings, fmt_metric='{value} mediums loaned'),
		nagiosplugin.ScalarContext('accountvalidity', w_validity, c_validity, fmt_metric='Account stil {value} days valid')
		)
	check.main(verbose=args.verbose,timeout=args.timeout)

if __name__ == '__main__':
	main()