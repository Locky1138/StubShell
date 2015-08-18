import StubShell
import sys
from BaseExecutables import Executable, TimedExe

from twisted.python import log
from twisted.internet import reactor


def main():
    users = {'usr': 'pas'}
    executables = [exe_wait]

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
