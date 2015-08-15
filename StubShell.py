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

# pulled directly by ShellProtocol, should be arguments?
GREETING = "welcome to the Test Shell"
PROMPT = "test_shell> "
# or maybe we should add EXECUTABLES here,
# instead of passing them down a long chain


# Executable Commands
class Executable(object):
    """Base class for all executable commands in the shell
    """
    def __init__(self, shell_protocol, cmd):
        self.shell = shell_protocol
        self.cmd = cmd['name']
        self.args = cmd['args']

    def run(self):
        self.main()
        self.end()

    def main(self):
        """main logic for the executable"""

    def end(self):
        """returns to the Shell's cmd_stack execution loop
        """
        self.shell.resume()


class exe_exit(Executable):
    """Every shell needs a basic exit command
    """
    name = 'exit'

    def main(self):
        log.msg('run exit()')
        self.shell.terminal.loseConnection()


class exe_command_not_found(Executable):
    """an executable to handle any un-expected commands
    """
    name = 'command_not_found'

    def main(self):
        log.err('command not found: %s' % self.cmd)
        self.shell.writeln(
            "StubShell: %s: command not found" % self.cmd
        )

'''
class exe_wait(Executable):
    """Temporarily Static executable
    will be refactored to use as a superclass for blockers
    """
    name = 'wait'

    def run(self):
        #self.shell.writeln("BEGIN")
        self.loopy(args[0])

    def loopy(self, i):
        d = defer.Deferred()
        if i > 0:
            self.shell.writeln("waiting...")
            d.addCallback(self.loopy)
            reactor.callLater(1, d.callback, i-1)
        else:
            #self.shell.writeln("DONE!")
            d.addCallback(self.end)
            d.callback(i)

    def end(self, i):
        self.shell.resume()
'''

# SSH Shell Configuration
class SSHRealm:
    """The realm connects application-specific objects to the
    authentication system.
    """
    implements(portal.IRealm)

    def __init__(self, executables):
        self.executables = executables

    def requestAvatar(self, avatarId, mind, *interfaces):
        return(
            interfaces[0],
            ShellAvatar(avatarId, self.executables),
            lambda: None
        )


class ShellAvatar(avatar.ConchUser):
    implements(interfaces.ISession)

    def __init__(self, username, executables):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.executables = executables
        self.channelLookup.update({'session': session.SSHSession})

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

    def connectionMade(self):
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
        if lines[-1] == ';':
            lines = lines[:-1]

        commands = []
        for line in lines.split(';'):
            words = line.split()
            cmd = {'name': words[0], 'args': []}
            if len(words) > 1:
                cmd['args'] = words[1:]
            commands.append(cmd)

        commands.reverse()
        self.cmd_stack += commands
        # now fire .run() on the command, to start it executing
        # It should execute the next command in the stack when complete
        # then return to waiting for lineReceived again
        self.resume()

    def run_cmd_stack(self):
        exe = self.get_executable(self.cmd_stack.pop())
        exe.run()
    
    def resume(self):
        """Used by Executables to signal their completion
        """
        if len(self.cmd_stack) > 0:
            self.run_cmd_stack()
        else:
            self.showPrompt() 

    def get_executable(self, cmd):
        """search for an executable that matches the command name
        """
        for exe in self.executables:
            if re.match(exe.name, cmd['name']):
                return exe(self, cmd)

        return exe_command_not_found(self, cmd)

    def writeln(self, data):
        self.terminal.write(data)
        self.terminal.nextLine()

    # Overriding to prevent terminal.reset()
    def initializeScreen(self):
        pass


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
    # create factroy authentication portal using SSHRealm
    ssh_factory.portal = portal.Portal(SSHRealm(executables))
    ssh_factory.portal.registerChecker(
        checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    )
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
    EXECUTABLES = [exe_wait]

    ssh_factory = get_ssh_factory(EXECUTABLES, **users)
    reactor.listenTCP(9999, ssh_factory)
    reactor.run()
