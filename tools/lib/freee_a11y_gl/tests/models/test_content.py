import pytest
from pathlib import Path
from freee_a11y_gl.models.content import Guideline
from freee_a11y_gl.relationship_manager import RelationshipManager
from freee_a11y_gl.models.faq.article import Faq

class TestGuideline:
    def test_init(self, all_check_data, setup_categories, setup_wcag_sc):
        """Test initialization of the Guideline class."""
        rel = RelationshipManager()
        guideline_data = {
            "id": "guideline1",
            "sortKey": "1",
            "category": "markup",
            "title": {"ja": "ガイドラインタイトル", "en": "Guideline Title"},
            "guideline": {"ja": "ガイドラインの内容", "en": "Guideline content"},
            "intent": {"ja": "ガイドラインの意図", "en": "Guideline intent"},
            "platform": ["web", "mobile"],
            "checks": ["0151", "0171"],
            "sc": ["1.1.1", "2.1.2"],
            "info": ["exp-markup-semantics", "exp-link-tab-order"],
            "src_path": "path/to/guideline.yaml"
        }
        guideline = Guideline(guideline_data)
        assert guideline.id == "guideline1"
        assert guideline.sort_key == "1"
        assert guideline.data.title == {"ja": "ガイドラインタイトル", "en": "Guideline Title"}
        assert guideline.data.guideline == {"ja": "ガイドラインの内容", "en": "Guideline content"}
        assert guideline.data.intent == {"ja": "ガイドラインの意図", "en": "Guideline intent"}
        assert guideline.data.platform == ["web", "mobile"]
        assert guideline.src_path == "path/to/guideline.yaml"
        assert guideline.object_type == "guideline"
        assert guideline.sort_key == "1"

        category = rel.get_related_objects(guideline, "category")[0]
        assert category.names == {"ja": "マークアップと実装", "en": "Markup and Implementation"}

        scs = rel.get_related_objects(guideline, "wcag_sc")
        assert len(scs) == 2
        assert set(guideline_data["sc"]) == set([sc.id for sc in scs])

        inforefs = rel.get_related_objects(guideline, "info_ref")
        assert len(inforefs) == 2
        assert set(guideline_data["info"]) == set([info.ref for info in inforefs])

    def test_duplicate_id(self, all_check_data, setup_categories, setup_wcag_sc):
        """Test duplicate ID handling."""
        guideline_data = {
            "id": "guideline1",
            "sortKey": "1",
            "category": "markup",
            "title": {"ja": "ガイドラインタイトル", "en": "Guideline Title"},
            "guideline": {"ja": "ガイドラインの内容", "en": "Guideline content"},
            "intent": {"ja": "ガイドラインの意図", "en": "Guideline intent"},
            "platform": ["web", "mobile"],
            "checks": ["0151", "0171"],
            "sc": ["1.1.1", "2.1.2"],
            "info": ["exp-markup-semantics", "exp-link-tab-order"],
            "src_path": "path/to/guideline.yaml"
        }
        Guideline(guideline_data)
        with pytest.raises(ValueError, match="Duplicate guideline ID: guideline1"):
            Guideline(guideline_data)

    def test_duplicate_sortkey(self, all_check_data, setup_categories, setup_wcag_sc):
        """Test duplicate sort key handling."""
        guideline_data1 = {
            "id": "guideline1",
            "sortKey": "1",
            "category": "markup",
            "title": {"ja": "ガイドラインタイトル", "en": "Guideline Title"},
            "guideline": {"ja": "ガイドラインの内容", "en": "Guideline content"},
            "intent": {"ja": "ガイドラインの意図", "en": "Guideline intent"},
            "platform": ["web", "mobile"],
            "checks": ["0151", "0171"],
            "sc": ["1.1.1", "2.1.2"],
            "info": ["exp-markup-semantics", "exp-link-tab-order"],
            "src_path": "path/to/guideline.yaml"
        }
        guideline_data2 = {
            **guideline_data1,
            **{"id": "guideline2", "sortKey": "1"}
        }
        Guideline(guideline_data1)
        with pytest.raises(ValueError, match="Duplicate guideline sortKey: 1"):
            Guideline(guideline_data2)

    def test_template_data(self, guideline_factory, setup_faq_tags):
        """Test generating template data."""
        sample_guideline = guideline_factory("markup/semantics")
        mock_faq = {
            "id": "faq1",
            "object_type": "faq",
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
        Faq(mock_faq)
        template_data = sample_guideline.template_data("ja")
        expected_template_data = {
            'id': 'gl-markup-semantics',
            'title': '文書構造を適切に示すマークアップ、実装を行う',
            'platform': 'Web、モバイル',
            'guideline': '静的なテキスト・コンテンツは、文書構造などのセマンティクスを適切に表現するHTMLの要素やコンポーネントで実装する。',
            'intent': 'スクリーン・リーダーなどの支援技術がコンテンツを正しく認識し、ユーザーに適切な形で提示できるようにする。\n\n-  適切なマークアップにより、スクリーン・リーダーで見出しや箇条書きの項目を探しやすくなる。\n-  スクリーン・リーダーなどの支援技術には、見出しやリンクの一覧表示機能など、適切なマークアップを前提に実装されている機能がある。',
            'category': 'マークアップと実装',
            'checks': [
                {
                    'id': '0541',
                    'check': '見出しとして表現されるべきものが、設計資料で明示されている。',
                    'severity': '[NORMAL]',
                    'target': 'デザイン',
                    'platform': 'Web、モバイル',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                },
                {
                    'id': '0542',
                    'check': '箇条書き、表などとして表現されるべきものが、使用するべきHTMLの要素やデザイン・システムのコンポーネントと共に、設計資料で明示されている。',
                    'severity': '[MAJOR]',
                    'target': 'デザイン',
                    'platform': 'Web',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                },
                {
                    'id': '0543',
                    'check': '見出しには適切な見出しレベルが指定されている：\n\n*  文書の階層構造を反映した見出しレベルが指定されている\n*  ページ全体では、見出しレベルは1から始まっている\n*  見出しレベルは、1の下位は2、2の下位は3のように1ずつ増加していて、抜けがない状態になっている',
                    'severity': '[NORMAL]',
                    'target': 'デザイン',
                    'platform': 'Web',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                },
                {
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
                },
                {
                    'id': '0552',
                    'check': '箇条書き、表などのセマンティクスが、設計資料に従って適切に実装されている。',
                    'severity': '[MAJOR]',
                    'target': 'コード',
                    'platform': 'Web',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'implementations': [
                        {
                            'title': 'セマンティクスに応じた実装',
                            'methods': [
                                {
                                    'platform': 'Web',
                                    'method': '*  箇条書き（ ``ul`` 、 ``ol`` 、 ``dl`` ）、表（ ``table`` ）などを使用する\n*  デザイン・システムの適切なコンポーネントを使用する'
                                }
                            ]
                        }
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                },
                {
                    'id': '0561',
                    'check': '見出しは、設計資料で示されている見出しレベルの見出しとしてスクリーン・リーダーに認識されている。',
                    'severity': '[NORMAL]',
                    'target': 'プロダクト',
                    'platform': 'Web、モバイル',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'conditions': [
                        {
                            'platform': 'Web',
                            'condition': '0561-content-00を満たしている、または(0561-axe-01を満たしている、かつ(0561-nvda-01または0561-macvo-01を満たしている))',
                            'procedures': [
                                {
                                    'id': '0561-content-00',
                                    'tool_display_name': 'その他の手段',
                                    'procedure': 'チェック対象は、見出しを含まないモーダル・ダイアログである。'
                                },
                                {
                                    'id': '0561-axe-01',
                                    'tool_display_name': 'axe DevTools',
                                    'procedure': 'axe DevToolsで以下のいずれの問題も出ない。\n\n*  :ref:`axe-rule-empty-heading`\n*  :ref:`axe-rule-heading-order`\n*  :ref:`axe-rule-page-has-heading-one`'
                                },
                                {
                                    'id': '0561-nvda-01',
                                    'tool_display_name': 'NVDA',
                                    'procedure': 'NVDAで以下の操作をして見出しリストを表示したとき、ページ中の見出しが過不足なく表示される。\n\n1. ブラウズ・モードで要素リストを表示（ :kbd:`NVDA+F7` ）\n2. 「種別」を「見出し」に設定（ :kbd:`Alt+H` ）',
                                    'YouTube': {'id': 'Gi2M1A0PB_0', 'title': '見出し【NVDAでアクセシビリティー チェック】'}
                                },
                                {
                                    'id': '0561-macvo-01',
                                    'tool_display_name': 'macOS VoiceOver',
                                    'procedure': 'macOS VoiceOverで以下の操作をして見出しリストを表示したとき、ページ中の見出しが過不足なく表示される。\n\n1. :kbd:`VO + U` を押下してローターのメニューを表示\n2. 「見出し」を選択'
                                }
                            ]
                        }
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                },
                {
                    'id': '0562',
                    'check': 'スクリーン・リーダーが、表を適切に認識していて、表中のセルも適切に認識している。',
                    'severity': '[MAJOR]',
                    'target': 'プロダクト',
                    'platform': 'Web、モバイル',
                    'guidelines': [
                        {'category': 'マークアップと実装', 'guideline': 'gl-markup-semantics'}
                    ],
                    'conditions': [
                        {
                            'platform': 'Web',
                            'condition': '0562-content-00または0562-nvda-01を満たしている',
                            'procedures': [
                                {
                                    'id': '0562-content-00',
                                    'tool_display_name': 'その他の手段',
                                    'procedure': 'チェック対象の画面に表が存在しない。'
                                },
                                {
                                    'id': '0562-nvda-01',
                                    'tool_display_name': 'NVDA',
                                    'procedure': '以下の手順で、ページ上のすべての表をNVDAで発見することができ、かつ、表中のセル間を移動して、セルの内容を適切に読み上げることができる。\n\n*  表の発見：\n\n   1. ブラウズ・モードでページの先頭に移動（ :kbd:`Ctrl+Home` ）\n   2. 前後の表への移動（ :kbd:`T` または :kbd:`Shift+T` キー）で、表に移動\n\n*  表中のセル間を移動して、セルの内容を読み上げる：\n\n   1. ブラウズ・モードで表の先頭部分を探す\n   2. 以下のキー操作でセル間を移動：\n\n      *  :kbd:`Ctrl+Alt+←` ： 左のセル\n      *  :kbd:`Ctrl+Alt+→` ： 右のセル\n      *  :kbd:`Ctrl+Alt+↓` ： 下のセル\n      *  :kbd:`Ctrl+Alt+↑` ： 上のセル', 'note': 'セル移動時に読み上げられる内容：\n\n上記のセル間移動の操作を行った場合、以下の内容が読み上げられます。\n\n*  左右の移動：移動先のセルの列見出し、列の番号、セルの内容\n*  上下の移動： 移動先のセルの行見出し、行の番号、セルの内容\n\nブラウズ・モードで単に矢印キーを操作した場合は、以下のような内容が読み上げられます。\n\n*  上下矢印： 前後のセルへ移動して読み上げ。ただしセル内で改行がある場合などは、セルの1部分だけが読み上げられることもある。\n*  左右矢印： 1文字ずつ移動して読み上げ。空のセルでは、1つだけスペースがあるような挙動になる。',
                                    'YouTube': {'id': 'lnW6TRgkBg0', 'title': '表【NVDAでアクセシビリティー チェック】'}
                                }
                            ]
                        }
                    ],
                    'info_refs': [
                        ':ref:`exp-markup-semantics`'
                    ]
                }
            ],
            'scs': [
                {
                    'sc': '1.3.1',
                    'level': 'A',
                    'LocalLevel': 'A',
                    'sc_en_title': 'Info and Relationships',
                    'sc_ja_title': '情報及び関係性',
                    'sc_en_url': 'https://www.w3.org/TR/WCAG21/#info-and-relationships',
                    'sc_ja_url': 'https://waic.jp/translations/WCAG21/#info-and-relationships'
                }
            ],
            'info': [
                ':ref:`exp-markup-semantics`'
            ],
            "faqs": ["faq1"]
        }
        check_keys = ["id", "title", "platform", "guideline", "intent", "category", "checks", "scs", "info", "faqs"]
        for key in check_keys:
            assert key in template_data
            assert template_data[key] == expected_template_data[key]
        assert template_data == expected_template_data

    def test_list_all_src_paths(self, guideline_factory, sample_dir):
        """Test listing all source paths using sample data."""
        sample_data = ["form/tab-order", "link/tab-order"]
        for gl in sample_data:
            guideline_factory(gl)
        expected_src_paths = [Path(f'{sample_dir}/data/yaml/gl/{gl}.yaml') for gl in sample_data]
        src_paths = Guideline.list_all_src_paths()
        assert len(src_paths) == len(expected_src_paths)
        assert set(expected_src_paths) == set(src_paths)

    def test_get_category_and_id(self, guideline_factory):
        """Test getting category and ID."""
        sample_guideline = guideline_factory("text/heading-label")
        category_data = sample_guideline.get_category_and_id("ja")
        assert category_data["category"] == "テキスト"
        assert category_data["guideline"] == "gl-text-heading-label"

    def test_link_data(self, guideline_factory):
        """Test generating link data."""
        sample_guideline = guideline_factory("form/tab-order")
        baseurl = "https://example.com"
        rel = RelationshipManager()
        category = rel.get_related_objects(sample_guideline, "category")[0]
        category_id = category.id
        category_name_ja = category.get_name("ja")
        category_name_en = category.get_name("en")
        expected_link_data = {
            "text": {
                "ja": f"{category_name_ja}：{sample_guideline.data.title["ja"]}",
                "en": f"{category_name_en}: {sample_guideline.data.title["en"]}"
            },
            "url": {
                "ja": f"{baseurl}/categories/{category_id}.html#{sample_guideline.id}",
                "en": f"{baseurl}/en/categories/{category_id}.html#{sample_guideline.id}"
            }
        }
        link_data = sample_guideline.link_data(baseurl)
        assert link_data == expected_link_data
