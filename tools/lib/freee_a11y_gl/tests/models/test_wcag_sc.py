import pytest
from freee_a11y_gl.models.reference import WcagSc

class TestWcagSc:
    def setup_method(self):
        """Set up test data."""
        self.sc1 = WcagSc(
            sc_id="1.1.1",
            sc={
                "id": "1.1.1",
                "sortKey": "001",
                "level": "A",
                "localPriority": "A",
                "ja": {"title": "非テキストコンテンツ", "url": "https://example.com/ja/1.1.1"},
                "en": {"title": "Non-text Content", "url": "https://example.com/en/1.1.1"}
            }
        )
        self.sc2 = WcagSc(
            sc_id="1.2.1",
            sc={
                "id": "1.2.1",
                "sortKey": "002",
                "level": "AA",
                "localPriority": "AA",
                "ja": {"title": "音声コンテンツ", "url": "https://example.com/ja/1.2.1"},
                "en": {"title": "Audio Content", "url": "https://example.com/en/1.2.1"}
            }
        )

    def test_init(self):
        """Test initialization of WcagSc."""
        assert self.sc1.id == "1.1.1"
        assert self.sc1.scnum == "1.1.1"
        assert self.sc1.sort_key == "001"
        assert self.sc1.level == "A"
        assert self.sc1.local_priority == "A"
        assert self.sc1.data.title["ja"] == "非テキストコンテンツ"
        assert self.sc1.data.title["en"] == "Non-text Content"
        assert self.sc1.data.url["ja"] == "https://example.com/ja/1.1.1"
        assert self.sc1.data.url["en"] == "https://example.com/en/1.1.1"

    def test_template_data(self):
        """Test retrieving template data."""
        template_data = self.sc1.template_data()
        assert template_data["sc"] == "1.1.1"
        assert template_data["level"] == "A"
        assert template_data["LocalLevel"] == "A"
        assert template_data["sc_en_title"] == "Non-text Content"
        assert template_data["sc_ja_title"] == "非テキストコンテンツ"
        assert template_data["sc_en_url"] == "https://example.com/en/1.1.1"
        assert template_data["sc_ja_url"] == "https://example.com/ja/1.1.1"

    def test_get_all(self):
        """Test retrieving all WcagSc instances sorted by sort_key."""
        all_sc = WcagSc.get_all()
        assert list(all_sc.keys()) == ["1.1.1", "1.2.1"]
        assert all_sc["1.1.1"] == self.sc1
        assert all_sc["1.2.1"] == self.sc2
