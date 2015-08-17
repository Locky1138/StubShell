# Run Me with 'trial tests/test_stub_shell.py'
from twisted.trial import unittest
import BaseExecutables
import base
from twisted.internet import task


PROMPT = base.StubShell.PROMPT

class exe_timed(BaseExecutables.TimedExe):
    name = "wait"
    first_print = "Begin Waiting:"
    final_print = "Waiting Complete"


EXECUTABLES = [exe_timed]


class BaseExecutablesTest(unittest.TestCase):

    def test_timed_executable(self):
        sp = base.get_shell_protocol()
        clock = task.Clock()
        exe = exe_timed(
            {'name': 'wait', 'args':[]},
            sp,
            clock
        )

        exe.run()

        self.assertEqual(
            sp.terminal.value(),
            "Begin Waiting:\n"
        )
        sp.terminal.clear()
        clock.advance(1)
    
        for _ in range(3):
            self.assertEqual(
                sp.terminal.value(),
                "waiting...\n"
            )
            sp.terminal.clear()
            clock.advance(1)

        self.assertEqual(
            sp.terminal.value(),
            "Waiting Complete\n" + PROMPT
        )
