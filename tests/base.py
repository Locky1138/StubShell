# Run Me with 'trial tests/test_stub_shell.py'
import StubShell
from twisted.test.proto_helpers import StringTransport
from BaseExecutables import Executable, TimedExe


PROMPT = StubShell.PROMPT
KEYPATH = '../keys'

class FakeTerminal(StringTransport):

    def __init__(self):
        StringTransport.__init__(self)

    # insults.RecvLine
    def LEFT_ARROW(self): pass
    def RIGHT_ARROW(self): pass
    def TAB(self): pass
    def BACKSPACE(self): pass
    def DELETE(self): pass
    def INSERT(self): pass  
    def HOME(self): pass
    def END(self): pass
    # insults.HistoricRecvLine
    def UP_ARROW(self): pass
    def DOWN_ARROW(self): pass
    def reset(self): pass

    def setModes(self, mode):
        self.mode = mode

    def nextLine(self):
        self.write('\n')


# Executables for testing
class exe_test_command(Executable):
    name = 'test_command'

    def main(self):
        self.shell.writeln("pass!")
        return 0


class exe_test_args(Executable):
    name = 'test_args'

    def main(self):
        self.shell.writeln("my args are: %s" % ", ".join(self.args))
        return 0


class exe_rexe(Executable):
    name = 'rexe(.*)'

    def main(self):
        self.shell.writeln("%s executed rexe" % self.cmd)
        return 0


class exe_wait(TimedExe):
    name = 'wait'
    first_print = "Begin Waiting:"
    final_print = "Waiting Complete"

    def __init__(self, cmd, shell_protocol):
        super(exe_wait, self).__init__(cmd, shell_protocol)
        self.count = int(self.args[0])


EXECUTABLES = [exe_test_command, exe_test_args, exe_rexe]


def build_factory():
    users = {'usr':'pas'}
    return StubShell.StubShellServer(EXECUTABLES, keypath=KEYPATH, **users)


def get_shell_protocol():
    sp = StubShell.ShellProtocol('usr', EXECUTABLES)
    sp.terminal = FakeTerminal()
    return sp
