from stubshell import StubShell 
from stubshell.BaseExecutables import get_executables 

import os
import sys
import argparse
from twisted.python import log
from twisted.internet import reactor


USERS = {'usr': 'pas'}

def main ():
    p = argparse.ArgumentParser(
        description='Supply StubShell with a .py file that defines your executable classes',
        usage='StubShell.py -c comand_config_file'
        )
    p.add_argument('-c','--config',
        help = 'config file(s)',
        dest = 'config_modules',
        nargs='+'
        )
    args = p.parse_args()

    print "loading executables from:"
    print args.config_modules


    EXES = []
    for cfg in args.config_modules:
        if not os.path.isfile(cfg):
            p.error('The file %s does not exist!' % cfg)

        EXES += get_executables(cfg)


    try:
        log.startLogging(sys.stderr)

        ss_server = StubShell.StubShellServer(
            EXES,
            **USERS
        )
        SERV = reactor.listenTCP(
            9999, 
            ss_server,
            interface='0.0.0.0')

        reactor.run()
    except KeyboardInterrupt:
        print "User interrupted"
        SERV.stopListening()
        sys.exit(1)
