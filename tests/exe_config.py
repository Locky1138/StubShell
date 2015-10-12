# Run Me with 'trial tests/test_stub_shell.py'
from stubshell.BaseExecutables import Executable, TimedExe


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
    name = 'rexe.*'

    def main(self):
        self.shell.writeln("%s executed rexe" % self.cmd)
        return 0


class exe_wait(TimedExe):
    name = 'wait'
    first_print = "Begin Waiting:"
    final_print = "Waiting Complete"

    def __init__(self, cmd, match, shell_protocol):
        super(exe_wait, self).__init__(cmd, match, shell_protocol)
        self.count = int(self.args[0])

