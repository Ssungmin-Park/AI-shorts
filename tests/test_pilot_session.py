"""Safety boundaries that must hold before any paid submission."""
import copy
import json
import unittest
from unittest.mock import Mock, patch

from shorts.pilot_session import JOURNAL, validate_submission, main


class PilotBudgetTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads(JOURNAL.read_text())
        for n in (2, 3):
            job = self.state["jobs"][str(n)]
            job.update(status="NOT_SUBMITTED", reserved_credits=0)
            job.pop("id", None)
        self.request = copy.deepcopy(self.state["jobs"]["2"]["request"])

    def test_uncertain_submission_blocks_paid_retry(self):
        self.state["jobs"]["2"].update(status="SUBMITTING", reserved_credits=25)
        with self.assertRaisesRegex(ValueError, "Existing/uncertain"):
            validate_submission(self.state, 2, self.request, 950)

    def test_unexpected_spend_blocks_next_submission(self):
        with self.assertRaisesRegex(ValueError, "Budget/balance"):
            validate_submission(self.state, 2, self.request, 925)

    def test_longer_generation_is_blocked_even_with_modified_journal(self):
        self.request["duration"] = 10
        self.state["jobs"]["2"]["request"] = self.request
        with self.assertRaisesRegex(ValueError, "five-second"):
            validate_submission(self.state, 2, self.request, 975)

    def test_completed_task_status_cannot_submit(self):
        state = copy.deepcopy(self.state)
        state["jobs"]["2"].update(id="existing-task", status="PENDING")
        with patch("sys.argv", ["pilot_session", "status", "--test", "2"]), \
             patch("shorts.pilot_session.JOURNAL", Mock(read_text=Mock(return_value=json.dumps(state)))), \
             patch("shorts.pilot_session.api", return_value={"status": "SUCCEEDED"}) as api, \
             patch("shorts.pilot_session.atomic_json"):
            main()
        api.assert_called_once_with("tasks/existing-task")

    def test_legacy_execute_cannot_bypass_tracked_journal(self):
        from shorts import pilot
        with patch("sys.argv", ["pilot", "--test", "2", "--execute"]), \
             patch("shorts.pilot.generate_scene") as generate:
            with self.assertRaisesRegex(ValueError, "legacy submission is blocked"):
                pilot.main()
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
