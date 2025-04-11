import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link


class TestA:
    """Test base anchor element macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.a({'value': 'x', 'href': 'x'}) }}", '<a href="x">x</a>'),
            (
                "{{ base.a({'value': 'x', 'href': 'x', 'external': True}) }}",
                '<a href="x">x <i class="far fa-external-link"></i></a>',
            ),
            (
                "{{ base.a({'value': 'x', 'href': 'x', 'class': 'x', 'foo': 'x'}) }}",
                '<a href="x" class="x" foo="x">x</a>',
            ),
            (
                "{{ base.a({'value': 'x', 'href': 'x', 'icon_pre': 'x', 'icon_post': 'x'}) }}",
                '<a href="x"><i class="x"></i> x <i class="x"></i></a>',
            ),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()

    def test_render_link(self, fx_lib_item_catalogue_jinja: Environment):
        """Can render macro with a Link class."""
        expected = BeautifulSoup('<a href="x">x</a>')
        link = Link(value="x", href="x")
        t = "{% import '_macros/base.html.j2' as base %}{{ base.a(link) }}"

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(source=t, globals={"link": link}).render())
        assert result.prettify() == expected.prettify()


class TestButton:
    """Test base button element macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.button({'value': 'x'}) }}", "<button>x</button>"),
            (
                "{{ base.button({'value': 'x', 'type': 'submit'}) }}",
                '<button type="submit">x</button>',
            ),
            (
                "{{ base.button({'value': 'x', 'href': 'x', 'icon_pre': 'x', 'icon_post': 'x'}) }}",
                '<button><i class="x"></i> x <i class="x"></i></button>',
            ),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()


class TestIStr:
    """Test base I (icon) element macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.i_str({'value': 'x'}) }}", "x"),
            (
                "{{ base.i_str({'value': 'x', 'icon_pre': 'x'}) }}",
                '<i class="x"></i> x',
            ),
            (
                "{{ base.i_str({'value': 'x', 'icon_post': 'x'}) }}",
                'x <i class="x"></i>',
            ),
            (
                "{{ base.i_str({'value': 'x', 'icon_pre': 'x', 'icon_post': 'x'}) }}",
                '<i class="x"></i> x <i class="x"></i>',
            ),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()


class TestImg:
    """Test base image element macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.img({'src': 'x'}) }}", '<img src="x" />'),
            ("{{ base.img({'src': 'x', 'foo': 'x'}) }}", '<img src="x" foo="x" />'),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()


class TestMailTo:
    """Test base 'mailto:' anchor element macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.mailto('x@example.com', 'x') }}", '<a href="mailto:x@example.com">x</a>'),
            ("{{ base.mailto('x@example.com') }}", '<a href="mailto:x@example.com">x@example.com</a>'),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()


class TestUlA:
    """Test base unordered list of anchor elements macro."""

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            ("{{ base.ul_a([]) }}", "<ul></ul>"),
            ("{{ base.ul_a([], 'x') }}", '<ul class="x"></ul>'),
            ("{{ base.ul_a([{'value': 'x', 'href': 'x'}]) }}", '<ul><li><a href="x">x</a></li></ul>'),
            (
                "{{ base.ul_a([{'value': 'x', 'href': 'x'}, {'value': 'y', 'href': 'y'}]) }}",
                '<ul><li><a href="x">x</a></li><li><a href="y">y</a></li></ul>',
            ),
            (
                "{{ base.ul_a([{'value': 'x', 'href': 'x', 'foo': 'x'}]) }}",
                '<ul><li><a href="x" foo="x">x</a></li></ul>',
            ),
        ],
    )
    def test_render(self, fx_lib_item_catalogue_jinja: Environment, value: str, expected_raw: str):
        """Can render macro."""
        expected = BeautifulSoup(expected_raw)
        t = "{% import '_macros/base.html.j2' as base %}" + value

        result = BeautifulSoup(fx_lib_item_catalogue_jinja.from_string(t).render())
        assert result.prettify() == expected.prettify()
