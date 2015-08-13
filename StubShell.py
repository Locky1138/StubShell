from zope.interface import implements
from twisted.cred import portal, checkers
from twisted.conch import avatar, interfaces, recvline
from twisted.conch.ssh import factory, userauth, connection, session, keys
from twisted.conch.insults import insults
import os
import sys
import re
from twisted.internet import reactor
from twisted.python import log

GREETING = "welcome to the Test Shell"
PROMPT = "test_shell> "


class Executable(object):

    def __init__(self, name):
        self.name = name

"""
class exe_test_command(Executable):
    name = 'test_command'
"""
    

class exe_exit(Executable):
    name = 'exit'

    def run(self):
        self.protocol.terminal.loseConnection()


# Generic SSHRealm
class SSHRealm:
    implements(portal.IRealm)
    def __init__(self, executables):
        self.executables = executables

    def requestAvatar(self, avatarId, mind, *interfaces):
        return interfaces[0], ShellAvatar(avatarId, self.executables), lambda: None


class ShellAvatar(avatar.ConchUser):
    implements(interfaces.ISession)

    def __init__(self, username, executabes):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.executables = executables
        self.channelLookup.update({'session':session.SSHSession})

    def openShell(self, protocol):
        shell_protocol = insults.ServerProtocol(
            ShellProtocol, 
            self,
            self.executables,
        )
        shell_protocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(shell_protocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        raise NotImplemented

    def closed(self):
        pass

    def eofReceived(self):
        pass


class ShellProtocol(recvline.HistoricRecvLine):
    def __init__(self, user, executables):
        self.user = user
        # FILO Stack
        self.cmd_stack = []
        self.executables = executables

    def connectionMade(self) : 
        recvline.HistoricRecvLine.connectionMade(self)
        self.terminal.reset = lambda: None 
        self.terminal.write(GREETING)
        self.terminal.nextLine()
        self.showPrompt()

    def showPrompt(self):
        self.terminal.write(PROMPT)

    def lineReceived(self, lines):
        """Split list of commands on ;
        split each command on spaces to
        create a dict representing the command name and args
        and append them to the cmd_stack in reverse order (FILO)
        """
        commands = [
            {'name':line.split()[0], 'args': line.split()[1:]} 
            for line in lines.split(';')
        ]
        commands.reverse()
        self.cmd_stack += commands
        """
        for cmd in commands:
            self.cmd_stack.append(cmd)

        for line in lines.split(';'):
            cmd = {'name':words[0], 'args': words[1:] in line.split()}
            self.cmd_stack.append(cmd)
        """

    def writeln(self, data):
        self.terminal.write(data)
        self.terminal.nextLine()

    #def loseConnection(self):
        # disable terminal reset, may not be needed
        #self.transport.loseConnection()

    # Overriding to prevent terminal.reset()
    def initializeScreen(self):
        pass

    def get_exe(self, cmd):
        for exe in self.executables:
            if re.match(cmd['name'], exe.name):
                return exe
    """
    class exe_exit(executable):
        name = 'exit'

        def call(self):
            self.protocol.terminal.loseConnection()
    """

def get_rsa_keys(keypath="keys"):
    pubkey = os.path.join(keypath, "public.key")
    privkey = os.path.join(keypath, "private.key")

    publicKeyString = file(pubkey).read()
    privateKeyString = file(privkey).read()
    return publicKeyString, privateKeyString


def get_ssh_factory(executables, keypath="./keys", **users):
    # create generic SSHFactory instance
    ssh_factory = factory.SSHFactory()
    # register credential checker
    checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    #ssh_factory.portal.registerChecker(checker)
    # create factroy authentication portal using SSHRealm
    ssh_factory.portal = portal.Portal(SSHRealm(executables))
    ssh_factory.portal.registerChecker(checker)
    # Set RSA Credentials
    pubkey, privkey = get_rsa_keys(keypath)
    ssh_factory.publicKeys = {
        'ssh-rsa': keys.Key.fromString(data=pubkey)
    }
    ssh_factory.privateKeys = {
        'ssh-rsa': keys.Key.fromString(data=privkey)
    }
    ssh_factory.services = {
        'ssh-userauth': userauth.SSHUserAuthServer,
        'ssh-connection': connection.SSHConnection
    }

    return ssh_factory



if __name__ == "__main__":
    log.startLogging(sys.stderr)
    users = {'usr': 'pas'}
    EXECUTABLES = []

    ssh_factory = get_ssh_factory(EXECUTABLES, **users)
    reactor.listenTCP(9999, ssh_factory)
    reactor.run()
