import unittest

from werkzeug.datastructures import MultiDict

import app as site


class ColorPaletteTests(unittest.TestCase):
    def test_clean_palette_migrates_legacy_slide_colors(self):
        palette = site._clean_palette({
            "primary": "#111111",
            "secondary": "#222222",
            "text": "#333333",
        })

        self.assertEqual(palette["primary"], "#111111")
        self.assertEqual(palette["secondary"], "#222222")
        self.assertEqual(palette["title_secondary"], "#111111")
        self.assertEqual(palette["body"], "#333333")
        self.assertEqual(palette["inverse"], "#222222")
        self.assertEqual(palette["subtitle"], "#333333")
        self.assertEqual(palette["projects_background"], site.PALETTE_DEFAULTS["projects_background"])
        self.assertEqual(palette["projects_title"], site.PALETTE_DEFAULTS["projects_title"])
        self.assertEqual(palette["projects_subtitle"], site.PALETTE_DEFAULTS["projects_subtitle"])
        self.assertEqual(palette["projects_body"], site.PALETTE_DEFAULTS["projects_body"])
        self.assertEqual(palette["label"], "#111111")
        self.assertNotIn("title", palette)
        self.assertNotIn("text", palette)

    def test_appearance_tab_exposes_all_named_color_roles(self):
        site.app.config["TESTING"] = True
        client = site.app.test_client()
        with client.session_transaction() as session:
            session["logged_in"] = True
        response = client.get("/admin")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for role in ("primary", "secondary", "title_primary", "title_secondary", "subtitle", "body", "muted", "label", "inverse"):
            self.assertIn(f"site_palette[{role}]", html)

    def test_appearance_tab_exposes_projects_section_palette_roles(self):
        site.app.config["TESTING"] = True
        client = site.app.test_client()
        with client.session_transaction() as session:
            session["logged_in"] = True
        html = client.get("/admin").get_data(as_text=True)
        for role in ("projects_background", "projects_title", "projects_subtitle", "projects_body"):
            self.assertIn(f"site_palette[{role}]", html)

    def test_appearance_save_updates_global_palette(self):
        original = site.load_data()
        try:
            site.app.config["TESTING"] = True
            client = site.app.test_client()
            with client.session_transaction() as session:
                session["logged_in"] = True
            values = {
                "title_primary": "#123456", "title_secondary": "#234567",
                "subtitle": "#345678", "body": "#456789", "muted": "#56789a",
                "label": "#6789ab", "inverse": "#789abc", "primary": "#89abcd",
                "secondary": "#9abcde", "projects_background": "#d4af0e",
                "projects_title": "#ffffff", "projects_subtitle": "#9b7200",
                "projects_body": "#ffffff",
            }
            form_data = {f"site_palette[{role}]": color for role, color in values.items()}
            response = client.post("/admin/appearance/save", data={"theme": "retro", **form_data})
            self.assertEqual(response.status_code, 200)
            saved = site.load_data()["site_palette"]
            for role, color in values.items():
                self.assertEqual(saved[role], color)
        finally:
            site.save_data(original)

    def test_collect_slides_accepts_named_palette_roles(self):
        fields = [
            ("slides[0][title]", "Title"),
            ("slides[0][desc]", "Description"),
            ("slides[0][hp]", "80"),
            ("slides[0][mode]", "text"),
        ]
        for role, value in site.PALETTE_DEFAULTS.items():
            fields.append((f"slides[0][color_palette][{role}]", "#123456"))

        slides = site.collect_slides(MultiDict(fields))

        self.assertEqual(len(slides), 1)
        self.assertEqual(set(slides[0]["color_palette"]), set(site.PALETTE_DEFAULTS))
        self.assertEqual(slides[0]["color_palette"]["subtitle"], "#123456")
        self.assertNotIn("text", slides[0])


if __name__ == "__main__":
    unittest.main()
