import os
import pytest


class TestExtractFileText:
    def test_extracts_text_from_pdf(self, mocker, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "test.pdf")
        with open(file_path, "w") as f:
            f.write("dummy")

        mock_reader = mocker.patch("pypdf.PdfReader")
        mock_page = mocker.MagicMock()
        mock_page.extract_text.return_value = "Sample PDF text"
        mock_reader.return_value.pages = [mock_page]

        result = extract_file_text(file_path)
        assert result == "Sample PDF text"

    def test_extracts_text_from_png(self, mocker, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "receipt.png")
        with open(file_path, "w") as f:
            f.write("dummy")

        mocker.patch(
            "pytesseract.image_to_string",
            return_value="OCR extracted text",
        )
        mocker.patch("PIL.Image.open")

        result = extract_file_text(file_path)
        assert result == "OCR extracted text"

    def test_extracts_text_from_jpg(self, mocker, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "receipt.jpg")
        with open(file_path, "w") as f:
            f.write("dummy")

        mocker.patch(
            "pytesseract.image_to_string",
            return_value="OCR from JPG",
        )
        mocker.patch("PIL.Image.open")

        result = extract_file_text(file_path)
        assert result == "OCR from JPG"

    def test_extracts_text_from_heic(self, mocker, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "receipt.heic")
        with open(file_path, "w") as f:
            f.write("dummy")

        mock_heif = mocker.patch("pyheif.read_heif")
        mock_heif_file = mocker.MagicMock()
        mock_heif.return_value = mock_heif_file

        mock_heif_file.mode = "RGB"
        mock_heif_file.stride = 3 * 100
        mock_heif_file.size = (100, 100)
        mock_heif_file.data = b"0" * (100 * 100 * 3)

        mocker.patch(
            "pytesseract.image_to_string",
            return_value="OCR from HEIC",
        )

        result = extract_file_text(file_path)
        assert result == "OCR from HEIC"

    def test_raises_on_unsupported_format(self, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "receipt.txt")
        with open(file_path, "w") as f:
            f.write("text")

        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_file_text(file_path)

    def test_raises_on_missing_file(self):
        from hsa_ledger.extractor import extract_file_text

        with pytest.raises(FileNotFoundError):
            extract_file_text("/nonexistent/receipt.pdf")

    def test_extracts_text_from_jpeg_extension(self, mocker, tmp_path):
        from hsa_ledger.extractor import extract_file_text

        file_path = os.path.join(tmp_path, "receipt.jpeg")
        with open(file_path, "w") as f:
            f.write("dummy")

        mocker.patch(
            "pytesseract.image_to_string",
            return_value="OCR from JPEG",
        )
        mocker.patch("PIL.Image.open")

        result = extract_file_text(file_path)
        assert result == "OCR from JPEG"
