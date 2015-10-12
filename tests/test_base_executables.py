# Run Me with 'trial tests/test_stub_shell.py'
from twisted.trial import unittest
from stubshell import BaseExecutables
import base
from twisted.internet import task

PROMPT = base.PROMPT


class BaseExecutablesTest(unittest.TestCase):

    def test_get_executables_from_file(self):
        exes = BaseExecutables.get_executables('../tests/exe_config.py')
        for exe in exes:
            self.assertTrue(
                issubclass(exe, 
                    (BaseExecutables.Executable, 
                    BaseExecutables.TimedExe)
                )
            )

    def test_timed_executable(self):

        class exe_timed(BaseExecutables.TimedExe):
            name = "wait"
            first_print = "Begin Waiting:"
            final_print = "Waiting Complete"


        sp = base.get_shell_protocol()
        clock = task.Clock()
        exe = exe_timed(
            {'name': 'wait', 'args':[]},
            {}, # standin for match
            sp,
            reactor=clock
        )

        exe.run()
        # first we print the first_print line
        self.assertEqual(
            sp.terminal.value(),
            "Begin Waiting:\n"
        )
        sp.terminal.clear()
        clock.advance(1)
        # then we see the output from print_timed_output
        # count times
        for _ in range(3):
            self.assertEqual(
                sp.terminal.value(),
                "waiting...\n"
            )
            sp.terminal.clear()
            clock.advance(1)
        # finally we see the final_print line, and prompt
        self.assertEqual(
            sp.terminal.value(),
            "Waiting Complete\n" + PROMPT
        )
