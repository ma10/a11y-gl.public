import pytest
from freee_a11y_gl.relationship_manager import RelationshipManager
from freee_a11y_gl.models.base import BaseModel
from unittest.mock import Mock

class TestRelationshipManager:
    def setup_method(self):
        """Set up a fresh instance of RelationshipManager for each test."""
        self.manager = RelationshipManager()
        self.manager._data = {}
        self.manager._unresolved_faqs = {}

    def test_singleton_behavior(self):
        """Test that RelationshipManager follows the singleton pattern."""
        manager1 = RelationshipManager()
        manager2 = RelationshipManager()
        assert manager1 is manager2

    def test_associate_objects(self):
        """Test associating two objects bidirectionally."""
        obj1 = Mock(spec=BaseModel, object_type="type1", id="id1")
        obj2 = Mock(spec=BaseModel, object_type="type2", id="id2")

        self.manager.associate_objects(obj1, obj2)

        # Check bidirectional relationship
        assert obj2 in self.manager._data["type1"]["id1"]["type2"]
        assert obj1 in self.manager._data["type2"]["id2"]["type1"]

    def test_add_unresolved_faqs(self):
        """Test adding unresolved FAQ relationships."""
        self.manager.add_unresolved_faqs("faq1", "faq2")

        # Check unresolved FAQs
        assert "faq2" in self.manager._unresolved_faqs["faq1"]
        assert "faq1" in self.manager._unresolved_faqs["faq2"]

    def test_resolve_faqs(self, mocker):
        """Test resolving unresolved FAQ relationships."""
        # Mock Faq model
        mock_faq1 = Mock()
        mock_faq1.id = "faq1"
        mock_faq1.object_type = "faq"
        mock_faq1.sort_key = 1
        mock_faq2 = Mock()
        mock_faq2.id = "faq2"
        mock_faq2.object_type = "faq"
        mock_faq2.sort_key = 2

        mocker.patch("freee_a11y_gl.models.faq.article.Faq.get_by_id", side_effect=lambda x: {"faq1": mock_faq1, "faq2": mock_faq2}.get(x))

        # Add unresolved FAQs
        self.manager.add_unresolved_faqs("faq1", "faq2")

        # Resolve FAQs
        self.manager.resolve_faqs()

        # Check that FAQs are associated
        assert mock_faq2 in self.manager._data[mock_faq1.object_type][mock_faq1.id][mock_faq2.object_type]
        assert mock_faq1 in self.manager._data[mock_faq2.object_type][mock_faq2.id][mock_faq1.object_type]

    def test_get_related_objects(self):
        """Test retrieving related objects of a specific type."""
        obj1 = Mock(spec=BaseModel, object_type="type1", id="id1")
        obj2 = Mock(spec=BaseModel, object_type="type2", id="id2")

        self.manager.associate_objects(obj1, obj2)

        related_objects = self.manager.get_related_objects(obj1, "type2")
        assert obj2 in related_objects

    def test_get_sorted_related_objects(self):
        """Test retrieving and sorting related objects."""
        obj1 = Mock(spec=BaseModel, object_type="type1", id="id1")
        obj2 = Mock(spec=BaseModel, object_type="type2", id="id2", sort_key=2)
        obj3 = Mock(spec=BaseModel, object_type="type2", id="id3", sort_key=1)

        self.manager.associate_objects(obj1, obj2)
        self.manager.associate_objects(obj1, obj3)

        sorted_objects = self.manager.get_sorted_related_objects(obj1, "type2")
        assert sorted_objects == [obj3, obj2]  # Sorted by sort_key