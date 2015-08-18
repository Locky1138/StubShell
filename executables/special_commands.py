from BaseExecutables import Executable

class exe_stty(Executable):
    """used for stty -echo, to disable echoing input
    """
    name = 'stty'

    def main(self):
        if self.args[0] == '-echo':
            self.shell.echo_on = False
            print "stty -echo disabled"
        else:
            self.shell.cmd_stack.append(
                {'name': self.cmd, 'args': self.args}
            )


class exe_ps1(Executable):
    """Allows us to set the prompt
    """
    name = 'PS1=(.+)'

    def main(self):
        seed = self.shell.cmd_match.group(1)
        self.shell.prompt = seed
        print "Prompt set to %s" % seed
