from stubshell.BaseExecutables import Executable
import re

class exe_stty(Executable):
    """used for stty -echo, to disable echoing input
    """
    name = 'stty'

    def main(self):
        if self.args[0] == '-echo':
            self.shell.echo_on = False
            print "stty -echo disabled"
            return 0
        else:
            self.shell.cmd_stack.append(
                {'name': self.cmd, 'args': self.args}
            )
            return 1
        

class exe_ps1(Executable):
    """Allows us to set the prompt
    """
    name = "PS1='(.+)'"

    def main(self):
        seed = self.match.group(1)
        self.shell.prompt = seed
        print "Prompt set to %s" % seed
        return 0


class exe_ps2(Executable):
    """dummy command, does nothing
    """
    name = "PS2="

    def main(self):
        print "Set PS2=''"
        return 0


class exe_echo(Executable):
    name = 'echo'

    def usage(self):
        self.shell.writeln("MockSSH: Expected usage: echo "
                     "My shell is: \d+ $0/$SHELL \d+"
                     "_my_return_code: $? __")
        return 1

    def main(self):
        if (len(self.args) == 6
            and self.args[0] == "My"
            and self.args[1] == "shell"
            and self.args[2] == "is:"
            ):
            seed = self.args[3]
            if self.args[4] == "$0":
                self.shell.writeln(
                    "My shell is: %s -bash %s" % (seed,seed)
                )
                return 0
            elif self.args[4] == "$SHELL":
                self.shell.writeln(
                    "My shell is: %s /bin/bash %s" % (seed,seed)
                )
                return 0
            else:
                self.usage()

        elif re.match(
            '"_\w+_return_code: \$\? __"',
            " ".join(self.args)
            ):
            self.shell.writeln(
                "%s %d __" % (self.args[0][1:], self.shell.RET)
            )
            return 0

        else:
            self.usage()
