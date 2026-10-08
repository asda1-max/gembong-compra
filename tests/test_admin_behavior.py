import re
import unittest

import app as site


class AdminBehaviorTests(unittest.TestCase):
    def setUp(self):
        site.app.config["TESTING"] = True
        self.client = site.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True

    def test_projects_tab_handler_is_rendered_and_carousel_copy_is_optional(self):
        html = self.client.get("/admin").get_data(as_text=True)

        self.assertIn('data-tab="projects"', html)
        self.assertIn("document.querySelectorAll('.tab-btn[data-tab]')", html)
        self.assertNotRegex(
            html,
            r'name="slides\[[^\"]+\]\[(?:title|desc)\]"[^>]*required',
        )
        self.assertIn("dan inline code.", html)

        scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
        self.assertTrue(scripts)
        script_source = "\n".join(scripts)
        self.assertNotIn("dan code", script_source)


if __name__ == "__main__":
    unittest.main()
