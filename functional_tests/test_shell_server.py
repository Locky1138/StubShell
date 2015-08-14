import unittest
import pexpect


class StubShellServerTest(unittest.TestCase):

    def setUp(self):
        # Log into the Test Shell using usr/pas authentication
        self.shell = pexpect.spawn('ssh -p 9999 usr@127.0.0.1')
        self.shell.expect('assword')
        self.shell.sendline('pas')
        self.shell.expect('test_shell> ')

    def tearDown(self):
        # Issue the exit command, and make sure we are disconnected
        self.shell.sendline('exit')
        self.shell.expect(pexpect.EOF)
        self.shell.close

    def test_unknown_command(self):
        # If we issue a non-existant command, it tells us
        self.shell.sendline('not_a_command bad args')
        self.shell.expect('StubShell: not_a_command: command not found')
        # then prompts for a new command
        self.shell.expect('test_shell> ')



if __name__ == '__main__':
    unittest.main()
