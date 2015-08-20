from zope.interface import implements
from twisted.cred import portal, checkers
from twisted.conch import avatar, interfaces, recvline
from twisted.conch.ssh import factory, userauth, connection, session, keys
from twisted.conch.insults import insults
import os
import sys
import re
from twisted.python import log

from BaseExecutables import exe_exit, exe_command_not_found

# pulled directly by ShellProtocol, should be arguments?
GREETING = "welcome to the Test Shell"
PROMPT = "test_shell> "
# or maybe we should add EXECUTABLES here,
# instead of passing them down a long chain



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
        self.prompt = PROMPT
        self.RET = 0
        self.executing = False
        self.echo_on = True
        self.mode = ''
        # FIFO Stack contains instances of executable commands
        self.cmd_stack = []
        self.cmd_list = []
        self.executables = executables
        self.executables += [exe_exit]

    def connectionMade(self):
        recvline.HistoricRecvLine.connectionMade(self)
        self.terminal.reset = lambda: None
        self.terminal.write(GREETING)
        self.terminal.nextLine()
        self.showPrompt()

    def characterReceived(self, ch, moreCharactersComing):
        """overriden to disable write(ch) if echo_on == False
        """
        if self.mode == 'insert':
            self.lineBuffer.insert(self.lineBufferIndex, ch)
        else:
            self.lineBuffer[self.lineBufferIndex:self.lineBufferIndex+1] = [ch]
        self.lineBufferIndex += 1
        if self.echo_on:
           self.terminal.write(ch)

    def showPrompt(self):
        self.terminal.write(self.prompt)

    def lineReceived(self, lines):
        """This is the Entry point into the Shell's executioner
        Split list of commands on ;
        split each command on spaces to
        create a dict representing the command name and args
        and append them to the cmd_stack (FIFO)
        """
        lines = lines.strip()
        if lines[-1] == ';':
            lines = lines[:-1]

        commands = []
        for line in lines.split(';'):
            words = line.split()
            cmd = {'name': words[0], 'args': []}
            if len(words) > 1:
                cmd['args'] = words[1:]
            commands.append(cmd)
        self.cmd_stack.append(commands)
        # now fire .run() on the command, to start it executing
        # It should execute the next command in the stack when complete
        # then return to waiting for lineReceived again
        if not self.executing:
            self.resume(self.RET)

    def resume(self, ret):
        """Used by Executables to signal their completion
        Check the current cmd_list for pending cmds
        Then check the cmd_stack for pending cmd(lists)
        when the stack is empty prompt
        """
        self.RET = ret
        if len(self.cmd_list) > 0:
            self.run_cmd_list()

        elif len(self.cmd_stack) > 0:
            self.executing = True
            self.cmd_list = self.cmd_stack.pop(0)
            self.run_cmd_list()

        else:
            self.executing = False
            self.showPrompt()


    def run_cmd_list(self):
        """what if we have exe.run() return a diferred
        that must return before we allow the shell to resume?
        that would allow us to take the return-code from the
        exe's defer, and add it to the Shell's env for get_return calls
        """
        cmd = self.cmd_list.pop(0)
        exe = self.get_executable(cmd)
        exe.run()
    

    def get_executable(self, cmd):
        """search for an executable that matches the command name
        """
        for exe in self.executables:
            match = re.match(exe.name, cmd['name'])
            if match:
                return exe(cmd, match, self)

        return exe_command_not_found(cmd, match, self)

    def writeln(self, data):
        log.msg("OUTPUT: %s" % data)
        self.terminal.write(data)
        self.terminal.nextLine()

    # Overriding to prevent terminal.reset()
    def initializeScreen(self):
        pass


class StubShellServer(factory.SSHFactory):
    """Factory (twisted.conch.ssh.factory.SSHFactory)
    buildProtocol method creates Protocol instances
    for each new connection
    """
    def __init__(self, executables, keypath="./keys", **users):
        # create factroy authentication portal using SSHRealm
        self.portal = portal.Portal(SSHRealm(executables))
        self.portal.registerChecker(
            checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
        )
        # Set RSA Credentials
        self.pub_key_file = os.path.join(keypath, "public.key")
        self.priv_key_file = os.path.join(keypath, "private.key")

        self.set_rsa_keys()

        self.services = {
            'ssh-userauth': userauth.SSHUserAuthServer,
            'ssh-connection': connection.SSHConnection
        }

    def set_rsa_keys(self):

        if not (os.path.exists(self.pub_key_file)
            and os.path.exists(self.priv_key_file)):
            self.generate_rsa_keys()

        pub_key_string = file(self.pub_key_file).read()
        priv_key_string = file(self.priv_key_file).read()

        self.publicKeys = {
            'ssh-rsa': keys.Key.fromString(data=pub_key_string)
        }
        self.privateKeys = {
            'ssh-rsa': keys.Key.fromString(data=priv_key_string)
        }

    def generate_rsa_keys(self):
        sys.stdout.write("Generating New RSA keypair... ")

        from Crypto.PublicKey import RSA
        from twisted.python import randbytes

        rsa_key = RSA.generate(1024, randbytes.secureRandom)
        file(self.pub_key_file, 'w+b').write(
            keys.Key(rsa_key).public().toString('openssh')
        )
        file(self.priv_key_file, 'w+b').write(
            keys.Key(rsa_key).toString('openssh')
        )
        
