import pytest
import datetime
from freee_a11y_gl.models.faq.article import Faq
from freee_a11y_gl.models.faq.tag import FaqTag
from freee_a11y_gl.models.content import Guideline
from freee_a11y_gl.models.check import Check
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

    def test__create_relationships(self, setup_faq_tags, all_guideline_data):
        """Test creating relationships with other objects."""
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
            "tags": ["axe"],
            "info": ["exp-tab-order-check"],
            "checks": ["0171"]
        }
        rel = RelationshipManager()
        faq = Faq(mock_faq)

        guidelines = rel.get_related_objects(faq, 'guideline')
        assert len(guidelines) == 1
        assert guidelines[0].id == 'gl-markup-semantics'

        tags = rel.get_related_objects(faq, 'faq_tag')
        assert len(tags) == 1
        assert tags[0].id == 'axe'

        info_refs = rel.get_related_objects(faq, 'info_ref')
        assert len(info_refs) == 1
        assert info_refs[0].id == 'exp-tab-order-check'

        checks = rel.get_related_objects(faq, 'check')
        assert len(checks) == 1
        assert checks[0].id == '0171'


    def test_link_data(self, faq_factory):
        """Test link data generation for FAQ."""
        faq = faq_factory("p0009")
        link_data = faq.link_data("https://example.com")
        expected_link_data = {
            "text": {
                "ja": "Safariでのみ、Tabキーによるフォーカス移動の挙動がおかしい",
                "en": "Focus Movement by Tab Key Is Strange Only in Safari"
            },
            "url": {
                "ja": "https://example.com/faq/articles/p0009.html",
                "en": "https://example.com/en/faq/articles/p0009.html"
            }
        }
        assert link_data == expected_link_data

    def test_get_dependency(self, faq_factory):
        """Test getting file dependencies for FAQ."""
        faq = faq_factory("p0009")
        sample_guideline_path = Guideline.get_by_id("gl-form-tab-order").src_path
        sample_check_path = Check.get_by_id("0171")
        dependency = faq.get_dependency()
        assert len(dependency) == 11
        assert faq.src_path in dependency
        assert sample_guideline_path in dependency

    def test_template_data(self, faq_factory):
        """Test template data generation for FAQ."""
        faq = faq_factory("p0009")
        faq_factory("d0001")
        RelationshipManager().resolve_faqs()
        template_data = faq.template_data("ja")
        expected_template_data = {
            'id': 'p0009',
            'title': 'Safariでのみ、Tabキーによるフォーカス移動の挙動がおかしい',
            'problem': 'SafariでWebページを表示して、 :kbd:`Tab` キーや :kbd:`Shift+Tab` キーでフォーカスを移動すると、本来フォーカスされるべきなのにスキップされる要素がある。\nGoogle Chromeや他のブラウザーでは適切にフォーカス移動できているが、コンテンツ側で何らかの対応が必要か。',
            'solution': 'デフォルト設定でSafariを使用している場合の挙動なので対処は不要。\n:kbd:`option+Tab` と :kbd:`Shift+option+Tab` キーを使用すると他のブラウザーと同様の挙動になる。',
            'explanation': 'デフォルト設定でSafariを使用している場合、リンクやボタンなど、本来 :kbd:`Tab` キーや :kbd:`Shift+Tab` キーでフォーカスを移動できるはずの要素の一部に、フォーカスが移動できません。\n代わりに、 :kbd:`option+Tab` キーや :kbd:`Shift+option+Tab` キーを使用すると、他のブラウザーと同様にフォーカスを移動できます。\n\nフォーカス順序のチェックをする場合、通常は他のブラウザーで確認して問題なければ問題はありません。\nもしSafariでチェックを実施する必要がある場合は、 :kbd:`option+Tab` キーと :kbd:`Shift+option+Tab` キーを使用して確認します。\n\nなお、macOS上のSafariを使用している場合は、以下のいずれかの設定をすることで、 :kbd:`Tab` キーと :kbd:`Shift+Tab` キーの挙動が他のブラウザーと同様になります。\n\n*  Safariの :menuselection:`設定 --> 詳細` で、「Tabキーを押したときにWebページ上の各項目を強調表示」にチェックを入れる\n*  macOSの :menuselection:`環境設定 --> アクセシビリティ --> キーボード` で「フルキーボードアクセス」を有効にする',
            'updated_str': '2025年3月25日',
            'tags': ['keyboard-operation'],
            'guidelines': [
                {'category': '入力ディバイス', 'guideline': 'gl-input-device-keyboard-operable'},
                {'category': '入力ディバイス', 'guideline': 'gl-input-device-focus'},
                {'category': '入力ディバイス', 'guideline': 'gl-input-device-focus-indicator'},
                {'category': 'リンク', 'guideline': 'gl-link-tab-order'},
                {'category': 'フォーム', 'guideline': 'gl-form-keyboard-operable'},
                {'category': 'フォーム', 'guideline': 'gl-form-tab-order'},
                {'category': 'フォーム', 'guideline': 'gl-form-dynamic-content-focus'},
                {'category': '動的コンテンツ', 'guideline': 'gl-dynamic-content-focus'}
            ],
            'checks': [
                {
                    'id': '0171',
                    'check': 'Tab/Shift+Tabキーによるフォーカス移動時の挙動は以下のすべてを満たしている：\n\n*  フォーカス・インジケーターまたはそれを代替する表示がある\n*  自動的に次のような挙動が発生しない：\n\n   -  フォームの送信\n   -  レイアウトの変更\n   -  ページの遷移\n   -  モーダル・ダイアログの表示\n   -  表示内容の大幅な変更'
                },
                {
                    'id': '0172',
                    'check': 'フォーカスの移動時、文脈、レイアウト、操作手順に即した自然な順序で、以下のコンポーネント間をフォーカスが移動する。\n\n*  リンクとボタン\n*  フォーム・コントロール（エディット・ボックス、チェックボックス、ラジオボタンなど）\n*  その他、マウスやキーボード、タッチによる操作を受け付けるすべてのもの'
                }
            ],
            "related_faqs": ["d0001"]
        }
        assert_keys = ["id", "title", "problem", "solution", "explanation", "updated_str", "tags", "guidelines", "related_faqs"]
        for key in assert_keys:
            assert template_data[key] == expected_template_data[key]
        assert len(template_data["checks"]) == len(expected_template_data["checks"])

        for i, check in enumerate(template_data["checks"]):
            assert check["id"] == expected_template_data["checks"][i]["id"]
            assert check["check"] == expected_template_data["checks"][i]["check"]

    def test_list_all(self, setup_faq_tags):
        """Test listing all FAQs by date."""
        faq1 = {
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
        faq2 = {
            **faq1,
            **{
                "id": "faq2",
                "sortKey": "2",
                "updated": "2023-09-01",
                "src_path": "path/to/faq2.yaml",
            }
        }
        faq3 = {
            **faq1,
            **{
                "id": "faq3",
                "sortKey": "3",
                "updated": "2023-12-01",
                "src_path": "path/to/faq3.yaml",
            }
        }
        Faq(faq1)
        Faq(faq2)
        Faq(faq3)
        all_faqs = Faq.list_all()
        assert len(all_faqs) == 3
        assert all_faqs[0].id == "faq1"
        assert all_faqs[1].id == "faq2"
        assert all_faqs[2].id == "faq3"

        all_faqs_by_date = Faq.list_all(sort_by="date")
        assert len(all_faqs_by_date) == 3
        assert all_faqs_by_date[0].id == "faq3"
        assert all_faqs_by_date[1].id == "faq1"
        assert all_faqs_by_date[2].id == "faq2"

    def test_list_all_src_paths(self, setup_faq_tags):
        """Test listing all FAQ source paths."""
        faq1 = {
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
        faq2 = {
            **faq1,
            **{
                "id": "faq2",
                "sortKey": "2",
                "updated": "2023-09-01",
                "src_path": "path/to/faq2.yaml",
            }
        }
        faq3 = {
            **faq1,
            **{
                "id": "faq3",
                "sortKey": "3",
                "updated": "2023-12-01",
                "src_path": "path/to/faq3.yaml",
            }
        }
        Faq(faq1)
        Faq(faq2)
        Faq(faq3)
        all_src_paths = Faq.list_all_src_paths()
        assert len(all_src_paths) == 3
        assert all_src_paths[0] == "path/to/faq1.yaml"
        assert all_src_paths[1] == "path/to/faq2.yaml"
        assert all_src_paths[2] == "path/to/faq3.yaml"

    def test_faq_relationship(self, setup_faq_tags):
        """Test FAQ relationships."""
        faq1 = {
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
        faq2 = {
            **faq1,
            **{
                "id": "faq2",
                "sortKey": "2",
                "updated": "2023-09-01",
                "src_path": "path/to/faq2.yaml",
                "faqs": ["faq3"]
            }
        }
        faq3 = {
            **faq1,
            **{
                "id": "faq3",
                "sortKey": "3",
                "updated": "2023-12-01",
                "src_path": "path/to/faq3.yaml",
                "faqs": ["faq1"]
            }
        }

        rel = RelationshipManager()
        faq1 = Faq(faq1)
        assert rel._unresolved_faqs == {}

        faq2 = Faq(faq2)
        assert rel._unresolved_faqs == {"faq2": ["faq3"], "faq3": ["faq2"]}

        faq3 = Faq(faq3)
        assert set(rel._unresolved_faqs["faq3"]) == set(["faq2", "faq1"])
        assert rel._unresolved_faqs["faq2"] == ["faq3"]
        assert rel._unresolved_faqs["faq1"] == ["faq3"]

        rel.resolve_faqs()
        faq1_related = rel.get_related_objects(faq1, "faq")
        assert len(faq1_related) == 1
        faq2_related = rel.get_related_objects(faq2, "faq")
        assert len(faq2_related) == 1
        faq3_related = rel.get_related_objects(faq3, "faq")
        assert len(faq3_related) == 2

        assert faq1_related[0].id == "faq3"
        assert faq2_related[0].id == "faq3"
        assert set([faq.id for faq in faq3_related]) == set(["faq1", "faq2"])
