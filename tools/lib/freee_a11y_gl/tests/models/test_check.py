import pytest
from freee_a11y_gl.models.check import Check
from freee_a11y_gl.relationship_manager import RelationshipManager
from freee_a11y_gl import info_utils
from freee_a11y_gl.models.reference import InfoRef
from unittest.mock import Mock
import os
import yaml

   
class TestCheck:
    def test_init(self):
        """Test initialization of Check."""
        check_data = {
            "id": "check1",
            "sortKey": "001",
            "check": {"en": "Check 1", "ja": "チェック1"},
            "severity": "high",
            "target": "target1",
            "platform": ["web"],
            "src_path": "/path/to/check1"
        }
        check = Check(check_data)
        assert check.id == "check1"
        assert check.sort_key == "001"
        assert check.check_text["en"] == "Check 1"
        assert check.severity == "high"
        assert check.target == "target1"
        assert check.platform == ["web"]
        assert check.src_path == "/path/to/check1"

    def test_duplicate_id(self):
        """Test that duplicate IDs raise an error."""
        check_data = {
            "id": "check1",
            "sortKey": "001",
            "check": {"en": "Check 1", "ja": "チェック1"},
            "severity": "high",
            "target": "target1",
            "platform": ["web"],
            "src_path": "/path/to/check1"
        }
        Check(check_data)
        with pytest.raises(ValueError, match="Duplicate check ID: check1"):
            Check(check_data)

    def test_duplicate_sort_key(self):
        """Test that duplicate sort keys raise an error."""
        check_data1 = {
            "id": "check1",
            "sortKey": "001",
            "check": {"en": "Check 1", "ja": "チェック1"},
            "severity": "high",
            "target": "target1",
            "platform": ["web"],
            "src_path": "/path/to/check1"
        }
        check_data2 = {
            "id": "check2",
            "sortKey": "001",
            "check": {"en": "Check 2", "ja": "チェック2"},
            "severity": "medium",
            "target": "target2",
            "platform": ["mobile"],
            "src_path": "/path/to/check2"
        }
        Check(check_data1)
        with pytest.raises(ValueError, match="Duplicate check sortKey: 001"):
            Check(check_data2)

    def test_template_data(self, guideline_factory):
        """Test generating template data."""
        rel = RelationshipManager()
        sample_guideline = guideline_factory("markup/semantics")
        sample_check = rel.get_sorted_related_objects(sample_guideline, 'check', key='id')[3]
        template_data = sample_check.template_data("ja")
        expected_template_data = {
            'id': '0551',
            'check': '見出しが、設計資料に従って適切に実装されている。',
            'severity': '[NORMAL]',
            'target': 'コード',
            'platform': 'Web、モバイル',
            'guidelines': [
                {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
            ],
            'implementations': [
                {
                    'title': '見出しの実装',
                    'methods': [
                        {
                            'platform': 'Web',
                            'method': '``h1`` ～ ``h6`` でマークアップする。'
                        },
                        {
                            'platform': 'iOS',
                            'method': '``UIAccessibilityTraits.header`` をセットする。'
                        },
                        {
                            'platform': 'Android',
                            'method': '当該テキストに対して ``android:accessiblityHeading`` を ``true`` に設定する（Android 9以降）'
                        }
                    ]
                }
            ],
            'info_refs': [
                ':ref:`exp-markup-semantics`'
            ]
        }
        assert template_data['id'] == '0551'
        assert template_data == expected_template_data

    def test_object_data(self, sample_dir, guideline_factory):
        """Test generating object data."""
        sample_guideline = guideline_factory("form/tab-order")
        rel = RelationshipManager()
        sample_check = rel.get_sorted_related_objects(sample_guideline, 'check', key='id')[0]
        info_links = info_utils.get_info_links(str(sample_dir))
        for info in InfoRef.list_all_internal():
            if info.ref in info_links:
                info.set_link(info_links[info.ref])
    
        object_data = sample_check.object_data()
        expected_object_data = {
            'id': '0172', 
            'sortKey': 501800, 
            'check': {
                'ja': 'フォーカスの移動時、文脈、レイアウト、操作手順に即した自然な順序で、以下のコンポーネント間をフォーカスが移動する。\n\n*  リンクとボタン\n*  フォーム・コントロール（エディット・ボックス、チェックボックス、ラジオボタンなど）\n*  その他、マウスやキーボード、タッチによる操作を受け付けるすべてのもの',
                'en': 'When moving the focus, the focus moves in a natural order that is consistent with the context, layout, and operating procedures among the following components.\n\n*  Links and Buttons\n*  Form controls\n*  Everything else that accepts mouse, keyboard, or touch operation'
            },
            'severity': '[NORMAL]',
            'target': 'product',
            'platform': ['web', 'mobile'],
            'guidelines': [
                {
                    'text': {'ja': 'フォーム：適切なフォーカス順序', 'en': 'Forms: Appropriate Focus Order'},
                    'url': {'ja': '/categories/form.html#gl-form-tab-order', 'en': '/en/categories/form.html#gl-form-tab-order'}
                }
            ],
            'info': [
                {
                    'text': {'ja': 'Tab/Shift+Tabキーを用いたチェック', 'en': 'Check Using Tab/Shift+Tab Keys'},
                    'url': {'ja': 'https://a11y-guidelines.freee.co.jp/explanations/tab-order-check.html#exp-tab-order-check', 'en': 'https://a11y-guidelines.freee.co.jp/en/explanations/tab-order-check.html#exp-tab-order-check'}
                }
            ],
            'conditions': [
                {
                    'type': 'simple',
                    'platform': 'web',
                    'procedure': {
                        'id': '0172-keyboard-01',
                        'platform': 'web',
                        'tool': 'keyboard',
                        'toolLink': {
                            'text': {'ja': 'キーボード操作', 'en': 'Keyboard'},
                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/keyboard.html#0172-keyboard-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/keyboard.html#0172-keyboard-01'}
                        },
                        'procedure': {
                            'ja': 'Tabキー、またはShift+Tabキーでフォーカスを移動したときの挙動は、以下を満たしている：\n\n*  すべてのリンク、ボタン、フォーム・コントロールおよび操作を受け付けるコンポーネントにフォーカスを移動できる\n*  フォーカスの移動順序は、文脈、レイアウト、操作手順に即した自然な順序になっている',
                            'en': 'Behavior when moving focus using the Tab key or Shift+Tab key fulfills the following:\n\n*  The focus moves to all the links, buttons, form controls, and components that accepts operation.\n*  The focus moves in a natural order that is consistent with the context, layout, and operating procedures.'
                        }
                    }
                },
                {
                    'type': 'simple',
                    'platform': 'ios',
                    'procedure': {
                        'id': '0172-iosvo-01',
                        'platform': 'ios',
                        'tool': 'ios-vo',
                        'toolLink': {
                            'text': {'ja': 'iOS VoiceOver', 'en': 'iOS VoiceOver'},
                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/ios-vo.html#0172-iosvo-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/ios-vo.html#0172-iosvo-01'}
                        },
                        'procedure': {
                            'ja': 'iOS VoiceOver有効時に1本指による左フリックおよび右フリックの操作でフォーカスを移動して、以下の点を確認する。\n\n*  選択状態の移動が、画面表示や表示内容の意味合いから考えて不自然な順序になっていない\n*  画面上に表示されているテキスト、表示されている画像の代替テキスト以外のものが読み上げられることがない\n*  画面上に表示されているもので読み上げられないものがない',
                            'en': 'Confirm the following by moving the focus with one-finger left/right flicks with iOS VoiceOver enabled:\n\n*  Selected state moves in a natural order that is consistent with displayed content and its meaning.\n*  Nothing besides text displayed on the screen and the alternative text of images being displayed is announced.\n*  Everything displayed on the screen is announced.'
                        }
                    }
                },
                {
                    'type': 'simple',
                    'platform': 'android',
                    'procedure': {
                        'id': '0172-androidtb-01',
                        'platform': 'android',
                        'tool': 'android-tb',
                        'toolLink': {
                            'text': {'ja': 'Android TalkBack', 'en': 'Android TalkBack'},
                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/android-tb.html#0172-androidtb-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/android-tb.html#0172-androidtb-01'}
                        },
                        'procedure': {
                            'ja': 'Android TalkBack有効時に1本指による左フリックおよび右フリックの操作でフォーカスを移動して、以下の点を確認する。\n\n*  選択状態の移動が、画面表示や表示内容の意味合いから考えて不自然な順序になっていない\n*  画面上に表示されているテキスト、表示されている画像の代替テキスト以外のものが読み上げられることがない\n*  画面上に表示されているもので読み上げられないものがない',
                            'en': 'Confirm the following by moving the focus with one-finger left/right flicks with Android TalkBack enabled:\n\n*  Selected state moves in a natural order that is consistent with displayed content and its meaning.\n*  Nothing besides text displayed on the screen and the alternative text of images being displayed is announced.\n*  Everything displayed on the screen is announced.'
                        }
                    }
                }
            ],
            'conditionStatements': [
                {
                    'platform': 'web',
                    'summary': {
                        'ja': '0172-keyboard-01を満たしている',
                        'en': '0172-keyboard-01 is true'
                    }
                }, 
                {
                    'platform': 'ios',
                    'summary': {
                        'ja': '0172-iosvo-01を満たしている',
                        'en': '0172-iosvo-01 is true'
                    }
                },
                {
                    'platform': 'android',
                    'summary': {
                        'ja': '0172-androidtb-01を満たしている',
                        'en': '0172-androidtb-01 is true'
                    }
                }
            ]
        }
        assert object_data == expected_object_data

    def test_list_all_src_paths(self, sample_dir):
        """Test listing all source paths using sample data."""
        # Load sample data
        sample_check_path = os.path.join(sample_dir, "checks", "sample_check.yaml")
        with open(sample_check_path, "r", encoding="utf-8") as file:
            check_data = yaml.safe_load(file)

        # Create Check instances
        for check in check_data:
            Check(check)

        # Verify source paths
        src_paths = Check.list_all_src_paths()
        assert len(src_paths) == len(check_data)
        for check in check_data:
            assert check["src_path"] in src_paths
