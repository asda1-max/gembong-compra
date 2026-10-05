import unittest
from html.parser import HTMLParser

import app as site


class AdminInputsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self.inputs.append(dict(attrs))


class AdminImageUploadTests(unittest.TestCase):
    def setUp(self):
        site.app.config["TESTING"] = True
        self.client = site.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in"] = True

    def test_carousel_image_field_is_upload_only(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)

        parser = AdminInputsParser()
        parser.feed(response.get_data(as_text=True))

        image_inputs = [
            item for item in parser.inputs
            if item.get("name", "").startswith("slides[")
            and item.get("name", "").endswith("][image]")
        ]
        image_file_inputs = [
            item for item in parser.inputs
            if item.get("name", "").startswith("slides[")
            and item.get("name", "").endswith("][image_file]")
        ]

        self.assertTrue(image_inputs, "saved image value should be retained internally")
        self.assertTrue(all(item.get("type") == "hidden" for item in image_inputs))
        self.assertTrue(image_file_inputs)
        self.assertTrue(all(item.get("type") == "file" for item in image_file_inputs))
        self.assertNotIn("IMAGE URL", response.get_data(as_text=True))

    def test_image_carousel_has_no_dark_overlay_layer(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="absolute inset-0 image-overlay"', response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
