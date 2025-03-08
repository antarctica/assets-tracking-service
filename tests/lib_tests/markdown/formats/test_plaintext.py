import pytest

from assets_tracking_service.lib.markdown.formats.plaintext import convert_to_plain_text


class TestPlainTextExtension:
    """Test plain text markdown extension."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("x", "x"),  # plain
            ("_x_", "x"),  # italic
            ("*x*", "x"),  # italic
            ("__x__", "x"),  # bold
            ("**x**", "x"),  # bold
            ("***x***", "x"),  # bold italic
            ("`x`", "x"),  # code
            ("# x", "x"),  # heading 1
            ("## x", "x"),  # heading 2
            ("### x", "x"),  # heading 3
            ("#### x", "x"),  # heading 4
            ("##### x", "x"),  # heading 5
            ("###### x", "x"),  # heading 6
            ("[x](y)", "x"),  # link
            ("![x](y)", ""),  # image (don't keep alt text)
            ("> x", "x"),  # blockquote
            ("> _x_", "x"),  # blockquote with nested element
            ("* x\n* y", "x\ny"),  # unordered list
            ("- x\n- y", "x\ny"),  # unordered list
            ("1. x\n2. y", "x\ny"),  # ordered list
            ("1. x\n1. y", "x\ny"),  # ordered list (alt)
            ("x\n---\ny", "x\ny"),  # horizontal rule
            ("```\nx\n```", "x"),  # code block/fence
            ("    x", "x"),  # code block/fence
        ],
    )
    def test_conversion(self, value: str, expected: str):
        """Can remove Markdown formatting as per commonmark spec."""
        result = convert_to_plain_text(value)
        assert result == expected

    def test_conversion_empty(self):
        """Can handle an empty string."""
        result = convert_to_plain_text("")
        assert result == ""

    def test_conversion_none(self):
        """Can handle a None value."""
        result = convert_to_plain_text(None)
        assert result == ""
