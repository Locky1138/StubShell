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

    def test_echo_off(self):
        # disable echo of input
        self.shell.sendline("stty -echo")
        self.shell.expect(PROMPT)
        self.shell.sendline("not_a_command")
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            # note that the command we typed is missing
            # and no return cariage
            "StubShell: not_a_command: command not found\r\n"
        )

        # Confirm default behavior after reconnecting
        self.tearDown()
        self.setUp()

        self.shell.sendline("not_a_command")
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            "not_a_command"
            "\r\nStubShell: not_a_command: command not found\r\n"
        )
    
    def test_set_ps1_commands(self):
        '''Note Pexpect sets a special prompt that it uses
        by changing it we are breaking its ability to check
        shell.before, so we just confirm that we can now expect
        the new prompt.
        '''
        self.shell.sendline("PS1='__special:123__>'")
        self.shell.expect('__special:123__>')
        self.shell.sendline("not_a_command")
        self.shell.expect('__special:123__>')


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
        cmd = 'echo "_my_return_code: $? __"'
        self.shell.sendline(cmd)
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            cmd + "\r\n"
            "_my_return_code: 0 __\r\n"
        )

        # and after command_not_found we should see $? = 127
        self.shell.sendline("not_a_command")
        self.shell.expect(PROMPT)
        self.shell.sendline(cmd)
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            cmd + "\r\n"
            "_my_return_code: 127 __\r\n"
        )

    def test_ps2_command(self):
        cmd = "PS2=''"
        self.shell.sendline(cmd)
        self.shell.expect(PROMPT)
        self.assertEqual(
            self.shell.before,
            cmd + "\r\n"
        )

