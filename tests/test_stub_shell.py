from twisted.trial import unittest
import StubShell 
from twisted.test.proto_helpers import StringTransport

from twisted.conch.ssh import factory
from twisted.cred import portal, checkers
from twisted.internet import reactor



class FakeTerminal(StringTransport):

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

    def run(self):
        self.shell.terminal.write("pass!")


class exe_rexe(StubShell.Executable):
    name = 'rexe.*'


EXECUTABLES = [exe_test_command, exe_rexe]
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
        sp.lineReceived("command")
        command = sp.cmd_stack[0]
        name = command['name']
        self.assertEqual(name, 'command')

    def test_lineReceived_with_args(self):
        sp = get_shell_protocol()
        sp.lineReceived("command arg0 arg1")
        command = sp.cmd_stack[0]
        name = command['name']
        args = command['args']
        self.assertEqual(name, 'command')
        self.assertEqual(args[0], 'arg0')
        self.assertEqual(args[1], 'arg1')

    def test_multiple_command_line(self):
        sp = get_shell_protocol()
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
        sp.lineReceived("test_command arg0")
        cmd = sp.cmd_stack.pop()
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, exe_test_command)
        self.assertEqual(exe.args[0], "arg0")

    def test_get_executable_regex(self):
        sp = get_shell_protocol()
        sp.lineReceived("rexe_something arg0")
        cmd = sp.cmd_stack.pop()
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, exe_rexe)
        
    def test_get_command_returns_command_not_found(self):
        sp = get_shell_protocol()
        sp.lineReceived("not_a_command arg0")
        sp.get_executable(sp.cmd_stack.pop())
        self.assertEqual(
            sp.terminal.value(),
            "StubShell: not_a_command: command not found\ntest_shell> "
        )


class ShellExecutableTest(unittest.TestCase):
    """Basic Commands to test
    exit, sudo, print, echo
    """

    def test_Executable_can_call_containing_shell(self):
        sp = get_shell_protocol()
        args = []
        exe = StubShell.Executable(sp, args)
        exe.shell.writeln("pass")
        self.assertEqual(sp.terminal.value(), "pass\n")


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


