import pytest
from freee_a11y_gl.models.check import Implementation, Method

@pytest.fixture
def implementation_data():
    """Fixture to create an Implementation instance for testing."""
    implementation = Implementation(
        title={"ja": "実装例", "en": "Implementation Example"},
        methods=[
            {"platform": "web", "method": {"ja": "手順1", "en": "Step 1"}},
            {"platform": "ios", "method": {"ja": "手順2", "en": "Step 2"}},
            {"platform": "android", "method": {"ja": "手順3", "en": "Step 3"}}
        ]
    )
    yield implementation
    
class TestImplementation:
    def test_post_init(self, implementation_data):
        """Test that __post_init__ converts methods to Method objects."""

        # Verify that methods are converted to Method objects
        assert len(implementation_data.methods) == 3
        assert isinstance(implementation_data.methods[0], Method)
        assert isinstance(implementation_data.methods[1], Method)
        assert isinstance(implementation_data.methods[2], Method)
        assert implementation_data.methods[0].platform == "web"
        assert implementation_data.methods[0].method["ja"] == "手順1"
        assert implementation_data.methods[0].method["en"] == "Step 1"
        assert implementation_data.methods[1].platform == "ios"

    def test_method_template_data(self, implementation_data):
        """Test the template_data method of Method class."""
        method = implementation_data.methods[0]
        assert method.template_data(lang="ja") == {
            "platform": "Web",
            "method": "手順1"
        }
        assert method.template_data(lang="en") == {
            "platform": "Web",
            "method": "Step 1"
        }

    def test_implementation_template_data(self, implementation_data):
        """Test the template_data method of Implementation class."""
        # Test template_data for Japanese
        result = implementation_data.template_data(lang="ja")
        assert result == {
            "title": "実装例",
            "methods": [
                {"platform": "Web", "method": "手順1"},
                {"platform": "iOS", "method": "手順2"},
                {"platform": "Android", "method": "手順3"}
            ]
        }

        # Test template_data for English
        result = implementation_data.template_data(lang="en")
        assert result == {
            "title": "Implementation Example",
            "methods": [
                {"platform": "Web", "method": "Step 1"},
                {"platform": "iOS", "method": "Step 2"},
                {"platform": "Android", "method": "Step 3"}
            ]
        }
