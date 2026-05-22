import pytest


class TestIsImagePath:
    def test_png_is_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.png") is True

    def test_jpg_is_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.jpg") is True
        assert _is_image_path("/vault/storage/abc123_receipt.jpeg") is True

    def test_gif_is_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.gif") is True

    def test_webp_is_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.webp") is True

    def test_pdf_is_not_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.pdf") is False

    def test_heic_is_not_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123_receipt.heic") is False

    def test_case_insensitive(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123.PNG") is True
        assert _is_image_path("/vault/storage/abc123.JPG") is True

    def test_no_extension_is_not_image(self):
        from hsa_ledger.ui import _is_image_path

        assert _is_image_path("/vault/storage/abc123") is False
