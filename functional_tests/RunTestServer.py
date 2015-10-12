# Hacky Test Server for FT's
# Run with: python -m functional_tests.RunTestServer

from stubshell import StubShell
import sys
from stubshell.BaseExecutables import get_executables 

from twisted.python import log
from twisted.internet import reactor


def main():
    users = {'usr': 'pas'}
    executables = get_executables('executables/special_commands.py')
    executables = get_executables('tests/exe_config.py')

    log.startLogging(sys.stderr)

    ss_server = StubShell.StubShellServer(
        executables,
        **users
    )
    SERV = reactor.listenTCP(
        9999, 
        ss_server,
        interface='0.0.0.0')

    reactor.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "User interrupted"
        SERV.stopListening()
        sys.exit(1)
