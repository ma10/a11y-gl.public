import pytest
import datetime
from freee_a11y_gl.models.faq.article import Faq
from freee_a11y_gl.models.faq.tag import FaqTag
from freee_a11y_gl.relationship_manager import RelationshipManager

class TestFaq:
    def test_init(self, all_guideline_data, setup_faq_tags):
        """Test initialization of FaqArticle."""
        mock_faq = {
            "id": "faq1",
            "sortKey": "1",
            "src_path": "path/to/faq1.yaml",
            "updated": "2023-10-01",
            "title": {"ja": "FAQタイトル", "en": "FAQ Title"},
            "problem": {"ja": "問題", "en": "Problem"},
            "solution": {"ja": "解決策", "en": "Solution"},
            "explanation": {"ja": "説明", "en": "explanation"},
            "guidelines": ["gl-markup-semantics"],
            "tags": ["axe"]
        }
        rel = RelationshipManager()
        faq = Faq(mock_faq)
        assert faq.id == "faq1"
        assert faq.sort_key == "1"
        assert faq.src_path == "path/to/faq1.yaml"
        assert faq.updated == datetime.datetime.fromisoformat("2023-10-01")
        assert faq.title == {"ja": "FAQタイトル", "en": "FAQ Title"}
        assert faq.problem == {"ja": "問題", "en": "Problem"}
        assert faq.solution == {"ja": "解決策", "en": "Solution"}
        assert faq.explanation == {"ja": "説明", "en": "explanation"}

        guidelines = rel.get_related_objects(faq, "guideline")
        assert len(guidelines) == 1
        assert guidelines[0].id == "gl-markup-semantics"
        tags = rel.get_related_objects(faq, "faq_tag")
        assert len(tags) == 1
        assert tags[0].id == "axe"

    def test_duplicate_id(self, setup_faq_tags):
        """Test duplicate FAQ ID raises ValueError."""
        mock_faq = {
            "id": "faq1",
            "sortKey": "1",
            "src_path": "path/to/faq1.yaml",
            "updated": "2023-10-01",
            "title": {"ja": "FAQタイトル", "en": "FAQ Title"},
            "problem": {"ja": "問題", "en": "Problem"},
            "solution": {"ja": "解決策", "en": "Solution"},
            "explanation": {"ja": "説明", "en": "explanation"},
            "tags": ["axe"]
        }
        Faq(mock_faq)
        with pytest.raises(ValueError, match="Duplicate FAQ ID: faq1"):
            Faq(mock_faq)

    def test_duplicate_sort_key(self, setup_faq_tags):
        """Test duplicate FAQ sortKey raises ValueError."""
        mock_faq1 = {
            "id": "faq1",
            "sortKey": "1",
            "src_path": "path/to/faq1.yaml",
            "updated": "2023-10-01",
            "title": {"ja": "FAQタイトル", "en": "FAQ Title"},
            "problem": {"ja": "問題", "en": "Problem"},
            "solution": {"ja": "解決策", "en": "Solution"},
            "explanation": {"ja": "説明", "en": "explanation"},
            "tags": ["axe"]
        }
        mock_faq2 = {
            **mock_faq1,
            **{"id": "faq2", "sortKey": mock_faq1["sortKey"]}
        }
        Faq(mock_faq1)
        with pytest.raises(ValueError, match="Duplicate FAQ sortKey: 1"):
            Faq(mock_faq2)

