from twisted.trial import unittest
from IPtomato import ssh_server
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


class exe_test_command(ssh_server.Executable):
    name = 'test_command'

    def run(self):
        self.shell.terminal.write("pass!")


EXECUTABLES = [exe_test_command]

def _build_factory():
    users = {'usr':'pas'}
    return ssh_server.get_ssh_factory(EXECUTABLES, keypath="..", **users)

# BEGIN TESTS
class ShellProtocolTest(unittest.TestCase):
    """Use Fake conch.insults.insults.ITerminalTransport
    """
    def get_shell_protocol(self):
        sp = ssh_server.ShellProtocol('usr', EXECUTABLES)
        sp.terminal = FakeTerminal()
        return sp

    def test_connection_made(self):
        sp = self.get_shell_protocol()
        sp.connectionMade()
        out = sp.terminal.value()
        expect_out = ssh_server.GREETING + "\n" + ssh_server.PROMPT
        self.assertEqual(out, expect_out)

    def test_write_line(self):
        sp = self.get_shell_protocol()
        sp.writeln("some output")
        out = sp.terminal.value()
        self.assertEqual(out, 'some output\n')

    def test_lineReceived_without_args(self):
        sp = self.get_shell_protocol()
        sp.lineReceived("command")
        command = sp.cmd_stack[0]
        name = command['name']
        self.assertEqual(name, 'command')

    def test_lineReceived_with_args(self):
        sp = self.get_shell_protocol()
        sp.lineReceived("command arg0 arg1")
        command = sp.cmd_stack[0]
        name = command['name']
        args = command['args']
        self.assertEqual(name, 'command')
        self.assertEqual(args[0], 'arg0')
        self.assertEqual(args[1], 'arg1')

    def test_multiple_command_line(self):
        sp = self.get_shell_protocol()
        sp.lineReceived("command0 arg0; command1 arg1.0 arg1.1")
        cmd2 = sp.cmd_stack[0]
        name = cmd2['name']
        args = cmd2['args']
        self.assertEqual(name, 'command1')
        self.assertEqual(args[0], 'arg1.0')
        self.assertEqual(args[1], 'arg1.1')

    def test_get_exe(self):
        sp = self.get_shell_protocol()
        sp.lineReceived("test_command")
        cmd = sp.cmd_stack.pop()
        exe = sp.get_exe(cmd)
        self.assertIs(exe, exe_test_command)

    def test_run_exe(self):
        sp = self.get_shell_protocol()
        sp.lineReceived("test_command")
        cmd = sp.cmd_stack.pop()
        exe = sp.get_exe(cmd)
        exe.run()
        out = sp.terminal.value()
        assertEqual(out, 'something')


class ShellExecutableTest(unittest.TestCase):
    """Basic Commands to test
    exit, sudo, print, echo
    """
    def test_execute_command(self):
        exe = ssh_server.Executable('test')
        exe.run()


class SSHRealmTest(unittest.TestCase):
    """Realm is used to create the authenticatin Portal in the ssh factory
    The Portal manages commnication between various authentication components
    including Realm, Avatar, and Credential Checkers
    """

    def test_create_ssh_factory_portal(self):
        ssh_factory = _build_factory()
        ssh_factory.portal = portal.Portal(ssh_server.SSHRealm(EXECUTABLES))

    def test_register_checkers(self):
        ssh_factory = _build_factory()
        ssh_factory.portal = portal.Portal(ssh_server.SSHRealm(EXECUTABLES))
       
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


