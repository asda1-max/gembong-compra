import io
import os
import tempfile
import unittest
from unittest.mock import patch

import app as site
from PIL import Image
from werkzeug.datastructures import FileStorage, MultiDict


class ProjectDetailTests(unittest.TestCase):
    def setUp(self):
        site.app.config["TESTING"] = True
        self.client = site.app.test_client()
        self.project = {
            "name": "Inventory Manager",
            "description": "A simple inventory platform.",
            "type": "Web App",
            "status": "active",
            "repo_url": "",
            "demo_url": "",
            "tags": [],
            "tech_stack": ["Python"],
            "detail_markdown": "",
        }

    def render_project(self, project):
        with patch.object(site, "_get_projects", return_value=[project]):
            return self.client.get("/projects/0")

    def test_optional_story_and_demo_are_hidden_when_empty(self):
        response = self.render_project(self.project)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("PROJECT STORY", html)
        self.assertNotIn("LIVE DEMO ↗", html)

    def test_markdown_story_renders_images_and_escapes_raw_html(self):
        project = dict(self.project)
        project["detail_markdown"] = (
            "## Tantangan\n- Kurangi proses manual\n"
            "![Dashboard](/static/uploads/dashboard.png)\n"
            "<script>alert('xss')</script>"
        )
        project["demo_url"] = "https://demo.example.com"
        response = self.render_project(project)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("PROJECT STORY", html)
        self.assertIn('<img class="story-image" src="/static/uploads/dashboard.png"', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert('xss')</script>", html)
        self.assertIn("LIVE DEMO ↗", html)

    def test_admin_tabs_work_and_carousel_copy_fields_are_optional(self):
        with self.client.session_transaction() as session:
            session["logged_in"] = True
        html = self.client.get("/admin").get_data(as_text=True)

        self.assertIn('data-tab="projects"', html)
        self.assertIn("document.querySelectorAll('.tab-btn[data-tab]')", html)
        self.assertNotRegex(
            html,
            r'name="slides\[[^\"]+\]\[(?:title|desc)\]"[^>]*required',
        )
        self.assertIn("dan inline code.", html)

    def test_project_banner_accepts_only_16_by_9_images(self):
        def image_file(width, height):
            stream = io.BytesIO()
            Image.new("RGB", (width, height), "#f2c94c").save(stream, format="PNG")
            stream.seek(0)
            return FileStorage(stream=stream, filename="banner.png", content_type="image/png")

        with tempfile.TemporaryDirectory() as upload_dir:
            form = MultiDict({
                "repos[0][name]": "Banner Test",
                "repos[0][description]": "",
                "repos[0][type]": "Web App",
                "repos[0][status]": "active",
            })
            with patch.object(site, "UPLOAD_FOLDER", upload_dir):
                project = site.collect_projects(
                    form,
                    {"repos[0][banner_file]": image_file(1600, 900)},
                )[0]
                self.assertTrue(project["banner"].startswith("/static/uploads/project-"))
                self.assertEqual(len(os.listdir(upload_dir)), 1)

                with self.assertRaisesRegex(ValueError, "16:9"):
                    site.collect_projects(
                        form,
                        {"repos[0][banner_file]": image_file(1000, 1000)},
                    )

    def test_collect_projects_supports_multiple_featured_projects(self):
        from werkzeug.datastructures import MultiDict

        form = MultiDict([
            ("repos[0][name]", "First"), ("repos[0][featured]", "1"),
            ("repos[1][name]", "Second"),
            ("repos[2][name]", "Third"), ("repos[2][featured]", "1"),
        ])
        projects = site.collect_projects(form)
        self.assertEqual([p["featured"] for p in projects], [True, False, True])
        self.assertEqual(
            [p["name"] for p in site._order_projects(projects)],
            ["First", "Third", "Second"],
        )


if __name__ == "__main__":
    unittest.main()
