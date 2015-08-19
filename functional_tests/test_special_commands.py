# First Start up a test server with -c executables/special_commands.py
# Run Me with 'trial functional_tests.test_shell_server.py'
import unittest
import pexpect
from StubShell import PROMPT


class SpecialCommandsTest(unittest.TestCase):
    """NOTE: these are tests for some weird edge cases that
    I have to deal with in my particular environment
    They should be good examples for some more complex
    command handling.
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

    def test_echo_my_shell_is(self):
        self.shell.sendline('echo My shell is: 123 $0 123')
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "echo My shell is: 123 $0 123\r\n"
            "My shell is: 123 -bash 123\r\n" 
        )

        self.shell.sendline('echo My shell is: 456 $SHELL 456')
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "echo My shell is: 456 $SHELL 456\r\n"
            "My shell is: 456 /bin/bash 456\r\n"
        )
        
    def test_echo_return_code(self):
        cmd = 'echo _my_return_code: $? __'
        self.shell.sendline(cmd)
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            cmd + "\r\n"
            "_my_return_code: 0 __\r\n"
        )

        # and after command_not_found we should see $? = 127
        cmd = 'not_a_command'
        self.shell.sendline(cmd)
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            cmd + "\r\n"
            "_my_return_code: 127 __\r\n"
        )


