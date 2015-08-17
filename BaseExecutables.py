from twisted.internet import reactor, defer


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
