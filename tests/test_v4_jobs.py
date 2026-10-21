import copy
import json
import unittest

from shorts.project import ROOT
from shorts.v4_jobs import validate


class NewShotBudgetTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/"config/first-film-v4-plan.json").read_text())
        self.state=copy.deepcopy(self.plan)
        self.state.update(video_authorized_cap=144,starting_balance=921)
        for j in self.state["jobs"].values():
            j.update(status="NOT_SUBMITTED",reserved_credits=0);j.pop("id",None)
        self.name="wide_descent"

    def test_uncertain_submission_never_retries(self):
        self.state["jobs"][self.name]["status"]="SUBMITTING"
        with self.assertRaisesRegex(ValueError,"uncertain"):
            validate(self.state,self.plan,self.name,921)

    def test_longer_clip_is_not_covered_by_approval(self):
        for s in (self.plan,self.state):s["jobs"][self.name]["request"]["duration"]=5
        with self.assertRaisesRegex(ValueError,"three-second"):
            validate(self.state,self.plan,self.name,921)

    def test_hdr_surcharge_cannot_be_added(self):
        for s in (self.plan,self.state):s["jobs"][self.name]["request"]["outputFormat"]="hdr10"
        with self.assertRaisesRegex(ValueError,"surcharges"):
            validate(self.state,self.plan,self.name,921)

    def test_unexplained_spend_blocks_next_request(self):
        with self.assertRaisesRegex(ValueError,"mismatch"):
            validate(self.state,self.plan,self.name,900)


if __name__=="__main__":unittest.main()
