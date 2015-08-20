StubShell
=========

Create an SSH Server, with a shell that provides Stubbed Commands

Purpose
-------
For testing, emulate a server's SSH Shell interface and commands

Python
------
Runs on Python 2.7, until Twisted is updated to work on 3.4

conda_env.yaml is provided to set up a conda virtual environment

If you have miniconda or anaconda installed, run:
'''
conda create --StubShell --file conda_env.yaml
'''

Twisted
-------
Created using the [Twisted](https://twistedmatrix.com/trac/) framework

Esp. Twisted Conch for all the SSH magic.

Credits
-------
StubShell is derived from [MockSSH](https://github.com/ncouture/MockSSH),
which was derived from [kippo](https://github.com/desaster/kippo/), an SSH honeypot.

I used MockSSH for inspiration, and initial trials, but found it lacked some key features
that my application requires, so i am re-writing using TDD
