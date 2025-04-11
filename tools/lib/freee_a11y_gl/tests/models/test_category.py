import pytest
from freee_a11y_gl.models.content import Category

class TestCategory:
    def setup_method(self):
        """Set up test data."""
        self.category1 = Category(
            category_id="cat1",
            names={"ja": "カテゴリ1", "en": "Category 1"}
        )
        self.category2 = Category(
            category_id="cat2",
            names={"ja": "カテゴリ2", "en": "Category 2"}
        )

    def test_init(self):
        """Test initialization of Category."""
        assert self.category1.id == "cat1"
        assert self.category1.names["ja"] == "カテゴリ1"
        assert self.category1.names["en"] == "Category 1"
        assert Category._instances["cat1"] == self.category1

    def test_get_name(self):
        """Test retrieving localized names."""
        assert self.category1.get_name("ja") == "カテゴリ1"
        assert self.category1.get_name("en") == "Category 1"
        assert self.category1.get_name("fr") == "カテゴリ1"  # Fallback to Japanese

    def test_get_dependency(self, mocker):
        """Test retrieving dependencies."""
        # Mock related objects
        mock_guideline = mocker.Mock()
        mock_guideline.src_path = "/path/to/guideline"
        mock_check = mocker.Mock()
        mock_check.src_path = "/path/to/check"
        mock_faq = mocker.Mock()
        mock_faq.src_path = "/path/to/faq"

        # Mock relationship manager
        mocker.patch(
            "freee_a11y_gl.models.content.RelationshipManager.get_sorted_related_objects",
            return_value=[mock_guideline]
        )
        mocker.patch(
            "freee_a11y_gl.models.content.RelationshipManager.get_related_objects",
            side_effect=[[mock_check], [mock_faq]]
        )

        # Test dependencies
        dependencies = self.category1.get_dependency()
        assert dependencies == [
            "/path/to/guideline",
            "/path/to/check",
            "/path/to/faq"
        ]

    def test_list_all(self):
        """Test listing all Category instances."""
        all_categories = Category.list_all()
        assert len(all_categories) == 2
        assert self.category1 in all_categories
        assert self.category2 in all_categories
