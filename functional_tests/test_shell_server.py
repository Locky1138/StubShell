import unittest
import time
#import pexpect


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout


class ParamikoShellTest(unittest.TestCase):

    def test_connect_to_shell(self):
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
                username='usr',
                password='pas',
                port=9999,
                allow_agent=False,
                look_for_keys=False
        )

        channel = ssh.invoke_shell()
        recv_all(channel)
        trans = ssh.get_transport()
        self.assertTrue(trans.is_active())

        channel.send('exit\n')
        
        recv_all(channel)
        time.sleep(1)
        trans = ssh.get_transport()
        self.assertFalse(trans.is_active())

class CommandTests(unittest.TestCase):
    pass




if __name__ == '__main__':
    unittest.main()
