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
            "not_a_command bad args\r\n"
            "StubShell: not_a_command: command not found\r\n"
        )

    def test_slow_executable(self):
        # Still dont know a good way to test for the delays between outut
        # if we run an executable that prints output slowly
        self.shell.sendline('wait 3')
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "wait 3\r\n" +
            "waiting...\r\n" * 3
        )
        #expect("waiting...", timeout=2)
        #with assertError(pexpect timeout):
        #    expect(PROMPT, timeout=2)

if __name__ == '__main__':
    unittest.main()
