# first start the server with
# RunServer.py -c tests/exe_config.py
# Run Me with 'trial functional_tests.test_shell_server.py'
import unittest
import pexpect
from StubShell import PROMPT


class StubShellServerTest(unittest.TestCase):
    """These FT's run against a TestServer running on the local host
    they will confirm login/out functionality
    and mostly test the basic commands available in the shell
    """

    def setUp(self):
        # Log into the Test Shell using usr/pas authentication
        self.shell = pexpect.spawn('ssh -p 9999 usr@127.0.0.1')
        self.shell.expect('assword')
        self.shell.sendline('pas')
        self.shell.expect(PROMPT)

    def tearDown(self):
        # Issue the exit command, and make sure we are disconnected
        self.shell.sendline('exit')
        self.shell.expect(pexpect.EOF)
        self.shell.close

    def test_unknown_command(self):
        # If we issue a non-existant command, it tells us
        self.shell.sendline('not_a_command bad args')
        #self.shell.expect('StubShell: not_a_command: command not found')
        # then prompts for a new command
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "not_a_command bad args"
            "\r\nStubShell: not_a_command: command not found\r\n"
        )

    def test_slow_executable(self):
        # delay is checked by our unit tests
        self.shell.sendline('wait 3')
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "wait 3\r\n"
            "Begin Waiting:\r\n" +
            "waiting...\r\n" * 3 +
            "Waiting Complete\r\n"
        )

