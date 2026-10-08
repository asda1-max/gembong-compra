import json
import os
import tempfile
import unittest

import app as site


class PublicThemeTemplateTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = tempfile.TemporaryDirectory()
        self.original_data_file = site.DATA_FILE
        site.DATA_FILE = os.path.join(self.data_dir.name, "data.json")
        site.app.config["TESTING"] = True
        self.client = site.app.test_client()

    def tearDown(self):
        site.DATA_FILE = self.original_data_file
        self.data_dir.cleanup()

    def test_each_theme_renders_each_public_page_with_theme_layout(self):
        expected_pages = {
            "/": ("index", ("id=\"home\"", "id=\"carouselTrack\"", "class=\"dot")),
            "/projects": ("projects", ("repoSearch", "repoGrid", "featuredProject")),
            "/info": ("info", ("id=\"faqList\"", "id=\"contactForm\"", "name=\"message\"")),
        }
        for theme in site.THEMES:
            with self.subTest(theme=theme):
                data = site.load_data()
                data["theme"] = theme
                site.save_data(data)

                for path, (page, markers) in expected_pages.items():
                    with self.subTest(path=path):
                        response = self.client.get(path)
                        body = response.get_data(as_text=True)
                        self.assertEqual(response.status_code, 200)
                        for marker in markers:
                            self.assertIn(marker, body)
                        layout = "retro-arcade" if theme == "retro" else "modern-editorial" if theme == "modern" else "professional-corporate"
                        if theme == "retro":
                            self.assertIn(f'data-page-layout="{layout}"', body)
                        elif theme == "modern":
                            self.assertIn("--blue:#315df4", body)
                            self.assertIn("border-radius:24px", body)
                            self.assertIn("theme.js", body)
                        else:
                            self.assertIn("Georgia,serif", body)
                            self.assertIn("4px double", body)
                            self.assertIn("theme.js", body)

    def test_non_retro_templates_do_not_include_retro_templates(self):
        for theme in ("modern", "professional"):
            for page in ("index", "projects", "info"):
                with self.subTest(theme=theme, page=page):
                    with open(os.path.join(site.BASE_DIR, "templates", "themes", theme, f"{page}.html"), encoding="utf-8") as template:
                        source = template.read()
                    self.assertNotIn("themes/retro/", source)

    def test_visitor_theme_selection_changes_layout_and_persists_across_pages(self):
        data = site.load_data()
        data.setdefault("carousel", site.CAROUSEL)
        data.setdefault("contact", site.CONTACT_DEFAULTS)
        data.setdefault("content", site.CONTENT_DEFAULTS)
        data.setdefault("carousel_interval", site.INTERVAL_DEFAULT)
        site.save_data(data)
        response = self.client.post("/theme", json={"theme": "modern"})
        self.assertEqual(response.status_code, 204)
        self.assertIn("gembong_theme=modern", response.headers.get("Set-Cookie", ""))

        for path in ("/", "/projects", "/info"):
            with self.subTest(path=path):
                page = self.client.get(path).get_data(as_text=True)
                self.assertIn('data-page-layout="modern-editorial"', page)

    def test_invalid_visitor_theme_falls_back_to_admin_default(self):
        data = site.load_data()
        data.setdefault("carousel", site.CAROUSEL)
        data.setdefault("contact", site.CONTACT_DEFAULTS)
        data.setdefault("content", site.CONTENT_DEFAULTS)
        data.setdefault("carousel_interval", site.INTERVAL_DEFAULT)
        data["theme"] = "professional"
        site.save_data(data)
        self.client.set_cookie("gembong_theme", "not-a-theme")

        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('data-page-layout="professional-corporate"', page)


if __name__ == "__main__":
    unittest.main()
