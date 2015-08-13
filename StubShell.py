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

# Executable Commands
class Executable(object):
    """Base class for all executable commands in the shell
    """
    def __init__(self, shell_protocol, args):
        self.shell = shell_protocol
        self.args = args


class exe_exit(Executable):
    """Every shell needs a basic exit command
    """
    name = 'exit'

    def run(self):
        self.shell.terminal.loseConnection()


# SSH Shell Configuration
class SSHRealm:
    """The realm connects application-specific objects to the
    authentication system.
    """
    implements(portal.IRealm)
    def __init__(self, executables):
        self.executables = executables

    def requestAvatar(self, avatarId, mind, *interfaces):
        return interfaces[0], ShellAvatar(avatarId, self.executables), lambda: None


class ShellAvatar(avatar.ConchUser):
    implements(interfaces.ISession)

    def __init__(self, username, executables):
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
    """creates shell session, defines commands
    inject executable commands when the Factory creates the protocol instance
    Enter causes the line buffer to be cleared
    and the line to be passed to the lineReceived()
    """
    def __init__(self, user, executables=[]):
        self.user = user
        self.mode = ''
        # FILO Stack contains instances of executable commands
        self.cmd_stack = []
        self.executables = executables
        self.executables += [exe_exit]

    def connectionMade(self) : 
        recvline.HistoricRecvLine.connectionMade(self)
        self.terminal.reset = lambda: None 
        self.terminal.write(GREETING)
        self.terminal.nextLine()
        self.showPrompt()

    def showPrompt(self):
        self.terminal.write(PROMPT)

    def lineReceived(self, lines):
        """This is the Entry point into the Shell's executioner
        Split list of commands on ;
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
        # now fire .run() on the command, to start it executing
        # It should execute the next command in the stack when complete
        # or return here and wait for lineReceived again


    def writeln(self, data):
        self.terminal.write(data)
        self.terminal.nextLine()

    # Overriding to prevent terminal.reset()
    def initializeScreen(self):
        pass

    def get_executable(self, cmd):
        """search for an executable that matches the command name
        """
        for exe in self.executables:
            if re.match(exe.name, cmd['name']):
                return exe(self, cmd['args'])
        return self.command_not_found(cmd)

    def command_not_found(self, cmd):
        self.writeln("StubShell: %s: command not found" % cmd['name'])
        self.showPrompt()


# Functions for building and running the Server
def get_rsa_keys(keypath="keys"):
    pubkey = os.path.join(keypath, "public.key")
    privkey = os.path.join(keypath, "private.key")

    publicKeyString = file(pubkey).read()
    privateKeyString = file(privkey).read()
    return publicKeyString, privateKeyString


def get_ssh_factory(executables, keypath="./keys", **users):
    """Factory (twisted.conch.ssh.factory.SSHFactory)
    buildProtocol method creates Protocol instances
    for each new connection
    
    """
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
