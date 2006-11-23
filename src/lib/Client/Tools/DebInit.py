'''Debian Init Support for Bcfg2'''
__revision__ = '$Revision$'

import glob, os, re
import Bcfg2.Client.Tools

class DebInit(Bcfg2.Client.Tools.SvcTool):
    '''Debian Service Support for Bcfg2'''
    __name__ = 'DebInit'
    __execs__ = ['/usr/sbin/update-rc.d']
    __handles__ = [('Service', 'deb')]
    __req__ = {'Service': ['name', 'status']}
    svcre = re.compile("/etc/.*/[SK]\d\d(?P<name>\S+)")

    # implement entry (Verify|Install) ops
    def VerifyService(self, entry, _):
        '''Verify Service status for entry'''
        rawfiles = glob.glob("/etc/rc*.d/*%s" % (entry.get('name')))
        files = [filename for filename in rawfiles if \
                 self.svcre.match(filename).group('name') == entry.get('name')]
        if entry.get('status') == 'off':
            if files:
                entry.set('current_status', 'on')
                return False
            else:
                return True
        else:
            if files:
                return True
            else:
                entry.set('current_status', 'off')
                return False

    def InstallService(self, entry):
        '''Install Service for entry'''
        self.logger.info("Installing Service %s" % (entry.get('name')))
        try:
            os.stat('/etc/init.d/%s' % entry.get('name'))
        except OSError:
            self.logger.debug("Init script for service %s does not exist" % entry.get('name'))
            return False
        
        if entry.get('status') == 'off':
            self.cmd.run("/etc/init.d/%s stop" % (entry.get('name')))
            cmdrc = self.cmd.run("/usr/sbin/update-rc.d -f %s remove" % entry.get('name'))[0]
        else:
            cmdrc = self.cmd.run("/usr/sbin/update-rc.d %s defaults" % \
                                 (entry.get('name')))[0]
        return cmdrc == 0

    def FindExtra(self):
        '''Find Extra Debian Service Entries'''
        specified = [entry.get('name') for entry in self.getSupportedEntries()]
        extra = []
        for name in [self.svcre.match(fname).group('name') for fname in
                      glob.glob("/etc/rc[12345].d/S*") \
                      if self.svcre.match(fname).group('name') not in specified]:
            if name not in extra:
                extra.append(name)
        return [Bcfg2.Client.XML.Element('Service', name=name, type='deb') for name \
                in extra]

    def Remove(self, entries):
        '''Remove extra service entries'''
        self.logger.info('Removing services:')
        self.logger.info([entry.get('name') for entry in entries])
        for entry in entries:
            self.cmd.run("rm -f /etc/rc*.d/S??%s" % (entry.get('name')))
