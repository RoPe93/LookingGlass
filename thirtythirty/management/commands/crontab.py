
from django.core.management.base import BaseCommand

from optparse import make_option
import random

import thirtythirty.models
from thirtythirty.settings import PASSPHRASE_CACHE, LUKS
LUKS_CACHE = LUKS['key_file']

# we can't use USERNAME from thirtythirty.settings, as this is 'self-running' as root
USERNAME = 'pi'

Output = '/etc/cron.d/LookingGlass'

class Command(BaseCommand):
    args = '<NONE>'
    help = 'Output %s' % Output

    option_list = BaseCommand.option_list + (
        make_option('--print', '--dump', '-p',
                    action='store_true',
                    dest='print',
                    default=False,
                    help='Output what would be written to file',
                    ),
        )
    
    def handle(self, *args, **settings):
        P = thirtythirty.models.preferences.objects.first()
        Cache_Time = '*/30 * * * *'
        if P:
            Cache_Time = P.passphrase_cache_time
        Raw = """
SHELL=/bin/bash
MAILTO=root

# m h  dom mon dow username command

{reboot:20}{POWERUSER:8}/bin/chmod 755 /var/log

{recron:20}{POWERUSER:8}/home/{USERNAME}/.virtualenvs/thirtythirty/bin/python /home/{USERNAME}/thirtythirty/manage.py crontab

{random_minute:3} * * * * {USERNAME:8}/home/{USERNAME}/.virtualenvs/thirtythirty/bin/python /home/{USERNAME}/thirtythirty/manage.py update &>/dev/null

{daily:20}{POWERUSER:8}/usr/sbin/ntpdate -t1 pool.ntp.org &>/dev/null

{daily:20}{POWERUSER:8}/usr/bin/make --directory /etc/postfix reload &>/dev/null

{recron:20}{USERNAME:8}if [[ -e /tmp/address.wav ]]; then /usr/bin/aplay /tmp/address.wav; fi &>/dev/null

{daily:20}{USERNAME:8}/usr/bin/find /tmp -maxdepth 1 -type f -name '*sessionid*' -mtime +3 -delete &>/dev/null

{daily:20}{USERNAME:8}/usr/bin/find /home/{USERNAME}/Maildir -regex '.*:2\,[A-Z]*T[DF]*$' -type f -atime +3 -delete &>/dev/null

{daily:20}{USERNAME:8}/usr/local/bin/LookingGlass/add_jiggabytes.sh

# not filtering to /dev/null is LOUD
{frequently:20}{USERNAME:8}if [[ -e {cache_loc} ]]; then /home/{USERNAME}/.virtualenvs/thirtythirty/bin/python /home/{USERNAME}/thirtythirty/manage.py qmanage --run; fi &>/dev/null

{cachetime:20}{USERNAME:8}/home/{USERNAME}/.virtualenvs/thirtythirty/bin/python /home/{USERNAME}/thirtythirty/manage.py lockdb --lock --headless && shred -zu {cache_loc} &>/dev/null

{cachetime:20}{USERNAME:8}if [[ -e {cache_luks} ]]; then shred -zu {cache_luks}; fi &>/dev/null

""".format(**{
            'POWERUSER':'root',
            'USERNAME':USERNAME,
            'cache_loc':PASSPHRASE_CACHE,
            'cache_luks':LUKS_CACHE,
            'cachetime':Cache_Time,
            'daily':'@daily',
            'hourly':'@hourly',
            'random_minute':str(random.randrange(0, 60)),
            'reboot':'@reboot',
            'recron':'*/30 * * * *',
            'frequently':'*/10 * * * *',
        })
        if settings['print']:
            print Raw
        else:
            FH = file(Output, 'w')
            FH.write(Raw)
            FH.close()
