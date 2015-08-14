import unittest
import pexpect


class StubShellServerTest(unittest.TestCase):

    def test_connect_to_shell(self):
        shell = pexpect.spawn('ssh -p 9999 usr@127.0.0.1')
        shell.expect('assword')
        shell.sendline('pas')
        shell.expect('test_shell> ')

        shell.sendline('exit')
        shell.expect(pexpect.EOF)
        shell.close


    def test_unknown_command(self):
        shell = pexpect.spawn('ssh -p 9999 usr@127.0.0.1')
        shell.expect('assword')
        shell.sendline('pas')
        shell.expect('test_shell> ')

        shell.sendline('not_a_command bad args')
        shell.expect('StubShell: not_a_command: command not found')
        shell.expect('test_shell> ')


if __name__ == '__main__':
    unittest.main()
