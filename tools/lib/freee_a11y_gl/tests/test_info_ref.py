import pytest
from freee_a11y_gl.models.reference import InfoRef
from freee_a11y_gl.relationship_manager import RelationshipManager
from unittest.mock import Mock

class TestInfoRef:
    def setup_method(self):
        """Set up test data."""
        self.internal_ref = InfoRef("internal_ref")
        self.external_ref = InfoRef("https://example.com")
        self.pipe_ref = InfoRef("|custom|")

    def test_singleton_behavior(self):
        """Test that InfoRef follows the singleton pattern."""
        ref1 = InfoRef("internal_ref")
        ref2 = InfoRef("internal_ref")
        assert ref1 is ref2

    def test_init_internal_reference(self):
        """Test initialization of an internal reference."""
        assert self.internal_ref.ref == "internal_ref"
        assert self.internal_ref.internal is True

    def test_init_external_reference(self):
        """Test initialization of an external reference."""
        assert self.external_ref.ref == "https://example.com"
        assert self.external_ref.internal is False

    def test_refstring(self):
        """Test generating reference strings."""
        assert self.internal_ref.refstring() == ":ref:`internal_ref`"
        assert self.external_ref.refstring() == "https://example.com"
        assert self.pipe_ref.refstring() == "|custom|"

    def test_link_data_internal(self):
        """Test link data generation for internal references."""
        link_data = self.internal_ref.link_data()
        assert link_data["text"]["en"] == ":ref:`internal_ref`"
        assert link_data["url"]["en"] == ""

    def test_link_data_external(self):
        """Test link data generation for external references."""
        link_data = self.external_ref.link_data()
        assert link_data["text"]["en"] == "https://example.com"
        assert link_data["url"]["en"] == "https://example.com"

    def test_set_link(self):
        """Test setting link data manually."""
        custom_data = {
            "text": {"en": "Custom Text", "ja": "カスタムテキスト"},
            "url": {"en": "https://custom.com", "ja": "https://カスタム.com"}
        }
        self.internal_ref.set_link(custom_data)
        assert self.internal_ref.ref_data == custom_data

    def test_list_all_internal(self):
        """Test listing all internal references."""
        internal_refs = InfoRef.list_all_internal()
        assert self.internal_ref in internal_refs
        assert self.external_ref not in internal_refs

    def test_list_all_external(self):
        """Test listing all external references."""
        external_refs = InfoRef.list_all_external()
        assert self.external_ref in external_refs
        assert self.internal_ref not in external_refs

    def test_list_has_guidelines(self, mocker):
        """Test listing references associated with guidelines."""
        mock_guideline = Mock()
        mock_guideline.id = "guideline_id"
        mock_guideline.object_type = "guideline"
        mock_guideline.sort_key = 1
        rel = RelationshipManager()
        rel.associate_objects(self.internal_ref, mock_guideline)
        refs_with_guidelines = InfoRef.list_has_guidelines()
        assert self.internal_ref in refs_with_guidelines

    def test_list_has_faqs(self, mocker):
        """Test listing references associated with FAQs."""
        mock_faq = Mock()
        mock_faq.id = "faq_id"
        mock_faq.object_type = "faq"
        mock_faq.sort_key = 1
        rel = RelationshipManager()
        rel.associate_objects(self.internal_ref, mock_faq)
        refs_with_faqs = InfoRef.list_has_faqs()
        assert self.internal_ref in refs_with_faqs
