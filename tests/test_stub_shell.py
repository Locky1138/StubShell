# Run Me with 'trial tests/test_stub_shell.py'
import base
from stubshell import StubShell
from stubshell.BaseExecutables import Executable, TimedExe

from twisted.trial import unittest
from twisted.cred import portal, checkers
from twisted.internet import reactor, task, defer

PROMPT = base.PROMPT


class ShellProtocolTest(unittest.TestCase):
    """Use Fake conch.insults.insults.ITerminalTransport
    """
    def setUp(self):
        self.sp = base.get_shell_protocol()


    def test_connection_made(self):
        self.sp.connectionMade()
        out = self.sp.terminal.value()
        expect_out = StubShell.GREETING + "\n" + PROMPT
        self.assertEqual(out, expect_out)

    def test_write_line(self):
        self.sp.writeln("some output")
        out = self.sp.terminal.value()
        self.assertEqual(out, 'some output\n')

    def test_lineReceived_without_args(self):
        sp = base.get_shell_protocol()
        # disable running commands in the stack, so we can inspect it
        sp.resume = lambda x: None
        sp.lineReceived("command")
        command = sp.cmd_stack[0][0]
        name = command['name']
        self.assertEqual(name, 'command')

    def test_lineReceived_with_args(self):
        sp = base.get_shell_protocol()
        sp.resume = lambda x: None 
        sp.lineReceived("command arg0 arg1")
        command = sp.cmd_stack[0][0]
        name = command['name']
        args = command['args']
        self.assertEqual(name, 'command')
        self.assertEqual(args[0], 'arg0')
        self.assertEqual(args[1], 'arg1')

    def test_multiple_command_line(self):
        sp = base.get_shell_protocol()
        sp.resume = lambda x: None
        sp.lineReceived("command0 arg0; command1 arg1.0 arg1.1")
        cmd_list = sp.cmd_stack[0]
        cmd2 = cmd_list[1]
        name = cmd2['name']
        args = cmd2['args']
        self.assertEqual(name, 'command1')
        self.assertEqual(args[0], 'arg1.0')
        self.assertEqual(args[1], 'arg1.1')

    def test_exe_exit_in_shell_executables_by_default(self):
        sp = base.get_shell_protocol()
        self.assertIn(StubShell.exe_exit, sp.executables)

    def test_get_executable(self):
        sp = base.get_shell_protocol()
        cmd = {'name':'test_command', 'args':['arg0']}
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, base.exe_test_command)
        self.assertEqual(exe.args[0], "arg0")

    def test_get_executable_regex(self):
        sp = base.get_shell_protocol()
        cmd = {'name':'rexe_something', 'args':['arg0']}
        exe = sp.get_executable(cmd)
        self.assertIsInstance(exe, base.exe_rexe)

    def test_get_executable_regex_captures(self):
        sp = base.get_shell_protocol()
        cmd = {'name': 'rexe123', 'args':[]}
        exe = sp.get_executable(cmd)
        self.assertEqual(exe.match.group(1), '123') 
       
    def test_get_command_returns_command_not_found(self):
        sp = base.get_shell_protocol()
        sp.lineReceived("not_a_command arg0")
        #sp.get_executable(sp.cmd_stack.pop())
        self.assertEqual(
            sp.terminal.value(),
            "StubShell: not_a_command: command not found\n"
            + PROMPT
        )
        self.assertEqual(sp.RET, 127)

    def test_execute_multiple_commands(self):
        sp = base.get_shell_protocol()
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

    def test_received_new_input_while_running(self):
        sp = base.get_shell_protocol()
        sp.lineReceived(
            "test_command; "
            "test_args a1 a2; "
        )
        sp.lineReceived(
            "test_command; "
            "test_args b1 b2; "
        )
        self.assertEqual(
            sp.terminal.value(),
            "pass!\n"
            "my args are: a1, a2\n"
            + PROMPT +
            "pass!\n"
            "my args are: b1, b2\n"
            + PROMPT
        )



class ShellExecutableTest(unittest.TestCase):
    """Basic Commands to test
    exit, sudo, print, echo
    """

    def test_Executable_can_call_containing_shell(self):
        sp = base.get_shell_protocol()
        cmd = {'name':'test', 'args':[]}
        exe = Executable(cmd, {}, sp)
        exe.shell.writeln("pass")
        self.assertEqual(sp.terminal.value(), "pass\n")

    def test_exit_command_drops_connection(self):
        sp = base.get_shell_protocol()
        sp.lineReceived("exit")
        self.assertTrue(
            sp.terminal.disconnecting,
            "Shell did not call terminal.loseConnection()"
        )


class SSHRealmTest(unittest.TestCase):
    """Realm is used to create the authenticatin Portal in the ssh factory
    The Portal manages commnication between various authentication components
    including Realm, Avatar, and Credential Checkers
    """
    EXECUTABLES = []

    def test_create_ssh_factory_portal(self):
        ssh_factory = base.build_factory()
        ssh_factory.portal = portal.Portal(StubShell.SSHRealm(self.EXECUTABLES))

    def test_register_checkers(self):
        ssh_factory = base.build_factory()
        ssh_factory.portal = portal.Portal(StubShell.SSHRealm(self.EXECUTABLES))
       
        users = {'usr':'pas'}
        ssh_factory.portal.registerChecker(
            checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
        )


class ShellFactoryTest(unittest.TestCase):
    """The shell factory will be sent to the reactor to listen on a port
    it will handle incomming connections, authentication, and shell creation
    """

    def test_get_shell_factory_returns_SSHFactory(self):
        from twisted.conch.ssh import factory

        shell_factory = base.build_factory()
        self.assertIsInstance(shell_factory, factory.SSHFactory)

    def test_run_server_using_shell_factory(self):
        shell_factory = base.build_factory()
        listener = reactor.listenTCP(9998, shell_factory)
        listener.stopListening()


