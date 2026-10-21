import copy
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from shorts import project, runway


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.project = project.load_project()
        self.scene = self.project["scenes"][0]
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        patcher = patch.object(runway, "OUTPUT", self.output)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_timeline_and_generation_lengths(self):
        requests = [project.request_for(self.project, scene) for scene in self.project["scenes"]]
        self.assertEqual(sum(r["edit_duration"] for r in requests), 60)
        self.assertEqual(sum(r["duration"] for r in requests), 85)
        self.assertTrue(all(r["duration"] >= r["edit_duration"] for r in requests))
        self.assertEqual(requests[0]["image"], self.project["references"]["moon"])

    def test_invalid_timeline_rejected(self):
        invalid = copy.deepcopy(self.project)
        invalid["scenes"][1]["start"] = 4
        path = self.output / "invalid.json"
        project.atomic_json(path, invalid)
        with self.assertRaisesRegex(ValueError, "continuous"):
            project.load_project(path)

    def test_dry_run_cannot_call_api(self):
        client = Mock()
        with redirect_stdout(io.StringIO()):
            runway.generate_scene(self.project, self.scene, client=client)
        client.image_to_video.create.assert_not_called()
        self.assertFalse((self.output / "jobs").exists())

    def test_uncertain_submission_not_retried(self):
        client = Mock()
        client.image_to_video.create.side_effect = TimeoutError()
        with self.assertRaisesRegex(RuntimeError, "dashboard"):
            runway.generate_scene(self.project, self.scene, execute=True, client=client)
        with self.assertRaisesRegex(ValueError, "interrupted"):
            runway.generate_scene(self.project, self.scene, execute=True, client=client)
        self.assertEqual(client.image_to_video.create.call_count, 1)

    def test_existing_task_resumes_without_another_submission(self):
        client = Mock()
        client.image_to_video.create.return_value = SimpleNamespace(id="task-123")
        client.tasks.retrieve.return_value = SimpleNamespace(status="FAILED")
        with redirect_stdout(io.StringIO()):
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError, "failed"):
                    runway.generate_scene(self.project, self.scene, execute=True, client=client)
        self.assertEqual(client.image_to_video.create.call_count, 1)
        client.tasks.retrieve.assert_called_with("task-123")

    def test_changed_prompt_cannot_reuse_task(self):
        client = Mock()
        client.image_to_video.create.return_value = SimpleNamespace(id="task-123")
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            runway.generate_scene(self.project, self.scene, execute=True, client=client, timeout=0)
        changed = dict(self.scene, prompt=self.scene["prompt"] + " New take.")
        with self.assertRaisesRegex(ValueError, "different settings"):
            runway.generate_scene(self.project, changed, execute=True, client=client)
        self.assertEqual(client.image_to_video.create.call_count, 1)

    def test_pilot_jobs_do_not_collide_with_original_project(self):
        from shorts.pilot import load_tests
        pilot, requests = load_tests()
        self.assertEqual(sum(request["duration"] * 5 for request in requests), 75)
        client = Mock()
        client.image_to_video.create.return_value = SimpleNamespace(id="pilot-123")
        pilot_output = self.output / "pilot-tests"
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            runway.generate_scene(pilot, pilot["scenes"][0], execute=True, client=client,
                                  timeout=0, output_dir=pilot_output)
        self.assertTrue((pilot_output / "jobs/scene_01.json").is_file())
        self.assertFalse((self.output / "jobs/scene_01.json").exists())


if __name__ == "__main__":
    unittest.main()
