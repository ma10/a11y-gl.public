import pytest
from freee_a11y_gl.models.faq.tag import FaqTag
from freee_a11y_gl.relationship_manager import RelationshipManager
from unittest.mock import Mock

class TestFaqTag:
    def setup_method(self):
        """Set up test data."""
        self.tag1 = FaqTag(tag_id="tag1", names={"en": "Tag 1", "ja": "タグ1"})
        self.tag2 = FaqTag(tag_id="tag2", names={"en": "Tag 2", "ja": "タグ2"})

    def test_init(self):
        """Test initialization of FaqTag."""
        assert self.tag1.id == "tag1"
        assert self.tag1.names["en"] == "Tag 1"
        assert self.tag1.names["ja"] == "タグ1"
        assert FaqTag._instances["tag1"] == self.tag1

    def test_get_name(self):
        """Test retrieving localized tag names."""
        assert self.tag1.get_name("en") == "Tag 1"
        assert self.tag1.get_name("ja") == "タグ1"
        assert self.tag1.get_name("fr") == "タグ1"  # Fallback to Japanese

    def test_article_count(self, mocker):
        """Test counting related articles."""
        mock_rel = mocker.patch.object(RelationshipManager, "get_related_objects", return_value=[Mock(), Mock()])
        count = self.tag1.article_count()
        assert count == 2
        mock_rel.assert_called_once_with(self.tag1, "faq")

    def test_template_data(self, mocker):
        """Test generating template data."""
        mock_faq1 = Mock(id="faq1", sort_key=2)
        mock_faq2 = Mock(id="faq2", sort_key=1)
        mocker.patch.object(RelationshipManager, "get_related_objects", return_value=[mock_faq1, mock_faq2])

        template_data = self.tag1.template_data("en")
        assert template_data == {
            "tag": "tag1",
            "label": "Tag 1",
            "articles": ["faq2", "faq1"],  # Sorted by sort_key
            "count": 2
        }

    def test_template_data_no_articles(self, mocker):
        """Test template data when no articles are related."""
        mocker.patch.object(RelationshipManager, "get_related_objects", return_value=[])
        template_data = self.tag1.template_data("en")
        assert template_data is None

    def test_list_all(self, mocker):
        """Test listing all tags with optional sorting."""
        mocker.patch.object(FaqTag, "article_count", side_effect=[5, 2])

        # Default order
        all_tags = FaqTag.list_all()
        assert all_tags == [self.tag1, self.tag2]

        # Sort by count
        sorted_by_count = FaqTag.list_all(sort_by="count")
        assert sorted_by_count == [self.tag1, self.tag2]  # tag1 has more articles

        # Sort by label
        sorted_by_label = FaqTag.list_all(sort_by="label")
        assert sorted_by_label == [self.tag1, self.tag2]  # Alphabetical order
