from twisted.internet import reactor, defer
from twisted.python import log
import imp
import os

def get_executables(cfg_file):
    """This is some python magic that gets all of the executable
    classes out of a given config.py file
    """
    if not os.path.isfile(cfg_file):
        print "The file %s does not exist!" % cfg_file

    cfg_module = imp.load_source('cfg_module', cfg_file)
    #conf_module = __import__(config_file)

    md = cfg_module.__dict__
    return [
        md[k] for k in md if (
            isinstance(md[k], type) and md[k].__module__ == cfg_module.__name__
        )
    ]
    

# Template Classes
class Executable(object):
    """Base class for all executable commands in the shell
    """
    def __init__(self, cmd, shell_protocol):
        self.shell = shell_protocol
        self.cmd = cmd['name']
        self.args = cmd['args']

    def executor(self):
        """experiment:
        playing with returning a defered to the shellProtocol,
        which it should call back before continuing
        """
        d = defer.Deferred()
        d.addCallback(lambda noop: self.main())
        return d

    def main(self):
        """main logic for the executable"""

    def run(self):
        """what it do"""
        ret = self.main()
        self.shell.resume(ret)

    def end(self, ret):
        """returns to the Shell's cmd_stack execution loop
        """
        self.shell.resume(ret)


class TimedExe(Executable):
    """An executable that delays prompting for some period of time
    or prints output periodically.
    used for testing commands like ping, or things that timeout
    """
    first_print = None
    final_print = None
    count = 3
    delay = 1
    ret = 0   

    def __init__(self, cmd, shell_protocol, reactor=reactor):
        """We have to variabalize the reactor for testing with trial
        """
        super(TimedExe, self).__init__(cmd, shell_protocol)
        self.reactor = reactor

    def run(self):
        if self.first_print:
            self.shell.writeln(self.first_print)
        
        d = defer.Deferred()
        d.addCallback(self.loopy)
        self.reactor.callLater(self.delay, d.callback, self.count)


    def loopy(self, i):
        d = defer.Deferred()
        if i > 0:
            self.print_timed_output()
            d.addCallback(self.loopy)
            self.reactor.callLater(self.delay, d.callback, i-1)

        else:
            if self.final_print:
                d.addCallback(self.print_final_output)

            d.addCallback(self.end)
            d.callback(0)

    def print_timed_output(self):
        self.shell.writeln("waiting...")

    def print_final_output(self, ret):
        self.shell.writeln(self.final_print)
        return ret


# Executable Classes
# note that they have name attributes!
class exe_exit(Executable):
    """Every shell needs a basic exit command
    """
    name = 'exit'

    def main(self):
        log.msg('run exit()')
        self.shell.terminal.loseConnection()
        return 0


class exe_command_not_found(Executable):
    """an executable to handle any un-expected commands
    """
    name = 'command_not_found'

    def main(self):
        log.err('command not found: %s' % self.cmd)
        self.shell.writeln(
            "StubShell: %s: command not found" % self.cmd
        )
        return 127
