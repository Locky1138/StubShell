import StubShell
import sys
from BaseExecutables import get_executables 

from twisted.python import log
from twisted.internet import reactor




def main():
    users = {'usr': 'pas'}
    executables = get_executables('executables/special_commands.py')

    #Ugly patch to get FT working, should be loded with -c for FT's
    from tests.exe_config import exe_wait
    executables.append(exe_wait)


    log.startLogging(sys.stderr)

    ss_server = StubShell.StubShellServer(
        executables,
        **users
    )
    reactor.listenTCP(
        9999, 
        ss_server,
        interface='0.0.0.0')

    reactor.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "User interrupted"
        sys.exit(1)
