import copy
import json
import unittest

from shorts.project import ROOT
from shorts.revision_voice import validate


class VoiceBudgetTests(unittest.TestCase):
    def setUp(self):
        self.state=json.loads((ROOT/"docs/revision-v2-state.json").read_text())
        self.state["voice_status"]="NOT_SUBMITTED"
        self.state.pop("voice_task_id",None)
        self.request=copy.deepcopy(self.state["voice_request"])

    def test_unknown_submission_blocks_duplicate_charge(self):
        self.state["voice_status"]="SUBMITTING"
        with self.assertRaisesRegex(ValueError,"uncertain"):
            validate(self.state,self.request,925)

    def test_longer_script_cannot_exceed_approved_cap(self):
        self.request["promptText"]="가"*501
        self.state["voice_request"]=self.request
        with self.assertRaisesRegex(ValueError,"exceeds"):
            validate(self.state,self.request,925)

    def test_unexplained_balance_change_blocks_submission(self):
        with self.assertRaisesRegex(ValueError,"balance"):
            validate(self.state,self.request,921)


if __name__=="__main__":unittest.main()
