import pytest
import pandas as pd


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


class TestFilterReceiptRows:
    def test_returns_all_rows_with_file_path_when_no_search(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf", None, "b.pdf"],
            "provider": ["X", "Y", "Z"],
            "file_name": ["a.pdf", "y.pdf", "b.pdf"],
        })
        result = _filter_receipt_rows(df)
        assert len(result) == 2
        assert result.iloc[0]["provider"] == "X"
        assert result.iloc[1]["provider"] == "Z"

    def test_filters_by_provider_case_insensitive(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf", "b.pdf", "c.pdf"],
            "provider": ["Acme Dental", "Bright Care", "Acme Dental"],
            "file_name": ["a.pdf", "b.pdf", "c.pdf"],
        })
        result = _filter_receipt_rows(df, "acme")
        assert len(result) == 2
        assert (result["provider"] == "Acme Dental").all()

    def test_filters_by_file_name(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf", "b.pdf", "c.pdf"],
            "provider": ["A", "B", "C"],
            "file_name": ["receipt_001.pdf", "invoice_002.pdf", "receipt_003.pdf"],
        })
        result = _filter_receipt_rows(df, "receipt")
        assert len(result) == 2
        assert list(result["file_name"]) == ["receipt_001.pdf", "receipt_003.pdf"]

    def test_excludes_rows_without_file_path(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": [None, None],
            "provider": ["A", "B"],
            "file_name": ["a.pdf", "b.pdf"],
        })
        result = _filter_receipt_rows(df)
        assert len(result) == 0

    def test_empty_result_when_no_match(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf"],
            "provider": ["Dental"],
            "file_name": ["receipt.pdf"],
        })
        result = _filter_receipt_rows(df, "nonexistent")
        assert len(result) == 0

    def test_regex_chars_are_literal(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf", "b.pdf"],
            "provider": ["ABC", "DEF"],
            "file_name": ["a.pdf", "b.pdf"],
        })
        result = _filter_receipt_rows(df, ".*")
        assert len(result) == 0

    def test_na_values_do_not_crash(self):
        from hsa_ledger.ui import _filter_receipt_rows

        df = pd.DataFrame({
            "file_path": ["a.pdf", "b.pdf"],
            "provider": [None, "ABC"],
            "file_name": [None, "b.pdf"],
        })
        result = _filter_receipt_rows(df, "abc")
        assert len(result) == 1


class TestPaginationInfo:
    def test_page_1_returns_first_page(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(25, 1, 10)
        assert info["page"] == 1
        assert info["start"] == 0
        assert info["end"] == 10
        assert info["total_pages"] == 3

    def test_page_2_returns_middle(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(25, 2, 10)
        assert info["page"] == 2
        assert info["start"] == 10
        assert info["end"] == 20
        assert info["total_pages"] == 3

    def test_last_page_has_remaining_items(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(25, 3, 10)
        assert info["page"] == 3
        assert info["start"] == 20
        assert info["end"] == 30
        assert info["total_pages"] == 3

    def test_page_clamped_when_exceeds_max(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(25, 5, 10)
        assert info["page"] == 3
        assert info["start"] == 20

    def test_page_clamped_when_below_min(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(25, 0, 10)
        assert info["page"] == 1
        assert info["start"] == 0

    def test_single_item_single_page(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(1, 1, 10)
        assert info["page"] == 1
        assert info["start"] == 0
        assert info["end"] == 10
        assert info["total_pages"] == 1

    def test_zero_items_returns_page_1(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(0, 1, 10)
        assert info["page"] == 1
        assert info["start"] == 0
        assert info["end"] == 10
        assert info["total_pages"] == 1

    def test_page_size_larger_than_total(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(3, 1, 10)
        assert info["page"] == 1
        assert info["start"] == 0
        assert info["end"] == 10
        assert info["total_pages"] == 1

    def test_exact_divisible(self):
        from hsa_ledger.ui import _pagination_info

        info = _pagination_info(20, 2, 10)
        assert info["page"] == 2
        assert info["start"] == 10
        assert info["end"] == 20
        assert info["total_pages"] == 2


class TestResolvePageOnSearch:
    def test_returns_1_when_search_changes(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("dentist", "", 3) == 1

    def test_keeps_page_when_search_unchanged(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("dentist", "dentist", 3) == 3

    def test_empty_to_nonempty_resets(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("new", "", 2) == 1

    def test_nonempty_to_empty_resets(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("", "old", 2) == 1

    def test_both_empty_keeps_page(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("", "", 1) == 1

    def test_case_sensitive_comparison(self):
        from hsa_ledger.ui import _resolve_page_on_search

        assert _resolve_page_on_search("Dentist", "dentist", 2) == 1
        assert _resolve_page_on_search("dentist", "Dentist", 2) == 1
