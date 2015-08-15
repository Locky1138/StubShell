# Run Me with 'trial tests/test_stub_shell.py'
from twisted.trial import unittest
import StubShell
from twisted.test.proto_helpers import StringTransport

from twisted.conch.ssh import factory
from twisted.cred import portal, checkers
from twisted.internet import reactor, defer


PROMPT = StubShell.PROMPT


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


class exe_test_command(StubShell.Executable):
    name = 'test_command'

    def main(self):
        self.shell.writeln("pass!")

class exe_test_args(StubShell.Executable):
    name = 'test_args'

    def main(self):
        self.shell.writeln("my args are: %s" % ", ".join(self.args))


class exe_rexe(StubShell.Executable):
    name = 'rexe.*'

    def main(self):
        self.shell.writeln("%s executed rexe" % self.cmd)


class exe_wait(StubShell.Executable):
    """Temporarily Static executable
    will be refactored to use as a superclass for blockers
    """
    name = 'wait'

    def run(self):
        #self.shell.writeln("BEGIN")
        self.loopy(int(self.args[0]))

    def loopy(self, i):
        d = defer.Deferred()
        if i > 0:
            self.shell.writeln("waiting...")
            d.addCallback(self.loopy)
            reactor.callLater(1, d.callback, i-1)
        else:
            #self.shell.writeln("DONE!")
            d.addCallback(self.end)
            d.callback(i)

    def end(self, i):
        self.shell.resume()


EXECUTABLES = [exe_wait, exe_test_command, exe_test_args, exe_rexe]
KEYPATH = '../keys'

def _build_factory():
    users = {'usr':'pas'}
    return StubShell.get_ssh_factory(EXECUTABLES, keypath=KEYPATH, **users)

def get_shell_protocol():
    sp = StubShell.ShellProtocol('usr', EXECUTABLES)
    sp.terminal = FakeTerminal()
    return sp


# BEGIN TESTS
class ShellProtocolTest(unittest.TestCase):
    """Use Fake conch.insults.insults.ITerminalTransport
    """

    def get_shell_protocol(self):
        sp = StubShell.ShellProtocol('usr', EXECUTABLES)
        sp.terminal = FakeTerminal()
        return sp

    def test_connection_made(self):
        sp = get_shell_protocol()
        sp.connectionMade()
        out = sp.terminal.value()
        expect_out = StubShell.GREETING + "\n" + StubShell.PROMPT
        self.assertEqual(out, expect_out)

    def test_write_line(self):
        sp = get_shell_protocol()
        sp.writeln("some output")
        out = sp.terminal.value()
        self.assertEqual(out, 'some output\n')

    def test_lineReceived_without_args(self):
        sp = get_shell_protocol()
        # disable running commands in the stack, so we can inspect it
        sp.run_cmd_stack = lambda: None
        sp.lineReceived("command")
        command = sp.cmd_stack[0]
        name = command['name']
        self.assertEqual(name, 'command')

    def test_lineReceived_with_args(self):
        sp = get_shell_protocol()
        sp.run_cmd_stack = lambda: None 
        sp.lineReceived("command arg0 arg1")
        command = sp.cmd_stack[0]
        name = command['name']
        args = command['args']
        self.assertEqual(name, 'command')
        self.assertEqual(args[0], 'arg0')
        self.assertEqual(args[1], 'arg1')

    def test_multiple_command_line(self):
        sp = get_shell_protocol()
        sp.run_cmd_stack = lambda: None
        sp.lineReceived("command0 arg0; command1 arg1.0 arg1.1")
        cmd2 = sp.cmd_stack[0]
        name = cmd2['name']
        args = cmd2['args']
        self.assertEqual(name, 'command1')
        self.assertEqual(args[0], 'arg1.0')
        self.assertEqual(args[1], 'arg1.1')

    def test_exe_exit_in_shell_executables_by_default(self):
        sp = get_shell_protocol()
        self.assertIn(StubShell.exe_exit, sp.executables)

    def test_get_executable(self):
        sp = get_shell_protocol()
        cmd = {'name':'test_command', 'args':['arg0']}
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, exe_test_command)
        self.assertEqual(exe.args[0], "arg0")

    def test_get_executable_regex(self):
        sp = get_shell_protocol()
        cmd = {'name':'rexe_something', 'args':['arg0']}
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, exe_rexe)
        
    def test_get_command_returns_command_not_found(self):
        sp = get_shell_protocol()
        sp.lineReceived("not_a_command arg0")
        #sp.get_executable(sp.cmd_stack.pop())
        self.assertEqual(
            sp.terminal.value(),
            "StubShell: not_a_command: command not found\n"
            + PROMPT
        )

    def test_execute_multiple_commands(self):
        sp = get_shell_protocol()
        sp.lineReceived(
            "test_command; "
            "test_args a1 a2; "
            "rexeisawesome;"
        )
        self.assertEqual(
            sp.terminal.value(),
            "pass!\n"
            "my args are: a1, a2\n"
            "rexeisawesome executed rexe\n"
            + PROMPT
        )


class ShellExecutableTest(unittest.TestCase):
    """Basic Commands to test
    exit, sudo, print, echo
    """

    def test_Executable_can_call_containing_shell(self):
        sp = get_shell_protocol()
        cmd = {'name':'test', 'args':[]}
        exe = StubShell.Executable(sp, cmd)
        exe.shell.writeln("pass")
        self.assertEqual(sp.terminal.value(), "pass\n")

    def test_exit_command_drops_connection(self):
        sp = get_shell_protocol()
        sp.lineReceived("exit")
        self.assertTrue(
            sp.terminal.disconnecting,
            "Shell did not call terminal.loseConnection()"
        )

    def test_waiting_executable(self):
        sp = get_shell_protocol()
        sp.lineReceived("wait 5")
        self.assertEqual(
            sp.terminal.value(),
            "waiting...\n"*5 + PROMPT
        )
        

class SSHRealmTest(unittest.TestCase):
    """Realm is used to create the authenticatin Portal in the ssh factory
    The Portal manages commnication between various authentication components
    including Realm, Avatar, and Credential Checkers
    """

    def test_create_ssh_factory_portal(self):
        ssh_factory = _build_factory()
        ssh_factory.portal = portal.Portal(StubShell.SSHRealm(EXECUTABLES))

    def test_register_checkers(self):
        ssh_factory = _build_factory()
        ssh_factory.portal = portal.Portal(StubShell.SSHRealm(EXECUTABLES))
       
        users = {'usr':'pas'}
        ssh_factory.portal.registerChecker(
            checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
        )


class ShellFactoryTest(unittest.TestCase):
    """The shell factory will be sent to the reactor to listen on a port
    it will handle incomming connections, authentication, and shell creation
    """

    def test_get_shell_factory_returns_SSHFactory(self):
        shell_factory = _build_factory()
        self.assertIsInstance(shell_factory, factory.SSHFactory)

    def test_run_server_using_shell_factory(self):
        shell_factory = _build_factory()
        listener = reactor.listenTCP(9998, shell_factory)
        listener.stopListening()


