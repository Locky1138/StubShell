import StubShell
import sys
from BaseExecutables import Executable, TimedExe

from twisted.python import log
from twisted.internet import reactor


class exe_wait(TimedExe):
    name = 'wait'
    first_print = "Begin Waiting:"
    final_print = "Waiting Complete"
    
    def __init__(self, cmd, shell_protocol):
        super(exe_wait, self).__init__(cmd, shell_protocol)
        self.count = int(self.args[0])
        



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
