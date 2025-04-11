import pytest
from pathlib import Path
from freee_a11y_gl.models.check import Check, Condition, Procedure

class TestCondition:
    def test_initialize_conditions(self, check_factory):
        """Test that conditions are initialized correctly in the Check instance."""
        sample_check = check_factory("product/0561")
        assert len(sample_check.conditions) == 3  # Assuming the sample data has 2 conditions
        assert isinstance(sample_check.conditions[0], Condition)
        assert isinstance(sample_check.conditions[1], Condition)
        assert isinstance(sample_check.conditions[2], Condition)

    def test_procedures(self, check_factory):
        """Test retrieving all procedures from a condition."""
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0].conditions[1].conditions[1]
        procedures = condition.procedures()
        assert len(procedures) == 2
        assert all(isinstance(proc, Procedure) for proc in procedures)

    def test_summary_simple(self, check_factory, mocker):
        """Test generating a summary for a simple condition."""
        sample_check = check_factory("product/0561")
        mock_settings_get = mocker.patch(
            "freee_a11y_gl.models.check.settings.get",
            side_effect=lambda key, default=None: {"locale.ja.pass_singular_text": "が正しい"}.get(key, default)
        )

        condition = sample_check.conditions[0].conditions[0]
        summary = condition.summary(lang="ja")
        assert summary == "0561-content-00が正しい"
        mock_settings_get.assert_called_with("locale.ja.pass_singular_text", " is true")

    def test_summary_complex(self, check_factory, mocker):
        """Test generating a summary for a complex condition."""
        sample_check = check_factory("product/0561")
        mock_settings_get = mocker.patch(
            "freee_a11y_gl.models.check.settings.get",
            side_effect=lambda key, default=None: {
                "locale.ja.list_separator": "、",
                "locale.ja.and_separator": "と",
                "locale.ja.or_separator": "または",
                "locale.ja.and_conjunction": "、かつ",
                "locale.ja.or_conjunction": "、または",
                "locale.ja.pass_singular_text": "を満たしている",
                "locale.ja.pass_plural_text": "を満たしている",
            }.get(key, default)
        )

        condition = sample_check.conditions[0]
        summary = condition.summary(lang="ja")
        assert summary == "0561-content-00を満たしている、または(0561-axe-01を満たしている、かつ(0561-nvda-01または0561-macvo-01を満たしている))"

    def test_template_data(self, check_factory, mocker):
        """Test generating template data for a condition."""
        sample_check = check_factory("product/0561")
        mock_settings_get = mocker.patch(
            "freee_a11y_gl.models.check.settings.get",
            side_effect=lambda key, default=None: {
                "platform.names.ja.web": "Web",
                "locale.ja.list_separator": "、",
                "locale.ja.and_separator": "と",
                "locale.ja.or_separator": "または",
                "locale.ja.and_conjunction": "、かつ",
                "locale.ja.or_conjunction": "、または",
                "locale.ja.pass_singular_text": "を満たしている",
                "locale.ja.pass_plural_text": "を満たしている",
            }.get(key, default)
        )

        expected_template_data = {
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

        condition = sample_check.conditions[0]
        template_data = condition.template_data(lang="ja")
        assert template_data == expected_template_data

    def test_object_data(self, check_factory):
        """Test generating object data for a condition."""
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0]
        expected_object_data = {
            'type': 'or',
            'platform': 'web',
            'conditions': [
                {
                    'type': 'simple',
                    'platform': 'web',
                    'procedure': {
                        'id': '0561-content-00',
                        'platform': 'web',
                        'tool': 'misc',
                        'toolLink': {
                            'text': {'ja': 'その他の手段', 'en': 'Miscellaneous Methods'},
                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/misc.html#0561-content-00', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/misc.html#0561-content-00'}
                        },
                        'procedure': {
                            'ja': 'チェック対象は、見出しを含まないモーダル・ダイアログである。',
                            'en': 'The target of the check is a modal dialog that does not contain any headings.'
                        }
                    }
                },
                {
                    'type': 'and',
                    'conditions': [
                        {
                            'type': 'simple',
                            'platform': 'web',
                            'procedure': {
                                'id': '0561-axe-01',
                                'platform': 'web',
                                'tool': 'axe',
                                'toolLink': {
                                    'text': {'ja': 'axe DevTools', 'en': 'axe DevTools'},
                                    'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/axe.html#0561-axe-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/axe.html#0561-axe-01'}
                                },
                                'procedure': {
                                    'ja': 'axe DevToolsで以下のいずれの問題も出ない。\n\n*  :ref:`axe-rule-empty-heading`\n*  :ref:`axe-rule-heading-order`\n*  :ref:`axe-rule-page-has-heading-one`',
                                    'en': 'None of the following issues is reported by axe DevTools.\n\n*  :ref:`axe-rule-empty-heading`\n*  :ref:`axe-rule-heading-order`\n*  :ref:`axe-rule-page-has-heading-one`'
                                }
                            }
                        },
                        {
                            'type': 'or',
                            'conditions': [
                                {
                                    'type': 'simple',
                                    'platform': 'web',
                                    'procedure': {
                                        'id': '0561-nvda-01',
                                        'platform': 'web',
                                        'tool': 'nvda',
                                        'toolLink': {
                                            'text': {'ja': 'NVDA', 'en': 'NVDA'},
                                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/nvda.html#0561-nvda-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/nvda.html#0561-nvda-01'}
                                        },
                                        'procedure': {
                                            'ja': 'NVDAで以下の操作をして見出しリストを表示したとき、ページ中の見出しが過不足なく表示される。\n\n1. ブラウズ・モードで要素リストを表示（ :kbd:`NVDA+F7` ）\n2. 「種別」を「見出し」に設定（ :kbd:`Alt+H` ）',
                                            'en': 'All headings on the page are displayed appropriately when displaying the heading list by steps below with NVDA.\n\n1. Display the elements list in browse mode (:kbd:`NVDA+F7`)\n2. Set the "Type" to "Headings" ():kbd:`Alt+H`)'
                                        },
                                        # 'youtube': {'id': 'Gi2M1A0PB_0', 'title': '見出し【NVDAでアクセシビリティー チェック】'}
                                    }
                                },
                                {
                                    'type': 'simple',
                                    'platform': 'web',
                                    'procedure': {
                                        'id': '0561-macvo-01',
                                        'platform': 'web',
                                        'tool': 'macos-vo',
                                        'toolLink': {
                                            'text': {'ja': 'macOS VoiceOver', 'en': 'macOS VoiceOver'},
                                            'url': {'ja': 'https://a11y-guidelines.freee.co.jp/checks/examples/macos-vo.html#0561-macvo-01', 'en': 'https://a11y-guidelines.freee.co.jp/en/checks/examples/macos-vo.html#0561-macvo-01'}
                                        },
                                        'procedure': {
                                            'ja': 'macOS VoiceOverで以下の操作をして見出しリストを表示したとき、ページ中の見出しが過不足なく表示される。\n\n1. :kbd:`VO + U` を押下してローターのメニューを表示\n2. 「見出し」を選択',
                                            'en': 'All headings on the page are displayed appropriately when displaying the heading list by steps below with macOS VoiceOver.\n\n1. Press :kbd:`VO + U` to display the rotor menu\n2. Select "Headings"'
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        object_data = condition.object_data()
        assert object_data == expected_object_data

class TestProcedure:
    def test_initialize_procedure(self, check_factory, mocker):
        """Test initializing a Procedure."""
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0].conditions[0]
        procedure = condition.procedure

        assert procedure.id == "0561-content-00"
        assert procedure.tool.id == "misc"
        assert procedure.procedure['ja'] == "チェック対象は、見出しを含まないモーダル・ダイアログである。"
        assert procedure.procedure['en'] == "The target of the check is a modal dialog that does not contain any headings."

    def test_template_data(self, check_factory, mocker):
        """Test generating template data for a Procedure."""
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0].conditions[1].conditions[0]
        procedure = condition.procedure

        expected_template_data = {
            'id': '0561-axe-01',
            'tool_display_name': 'axe DevTools',
            'procedure': 'axe DevToolsで以下のいずれの問題も出ない。\n\n*  :ref:`axe-rule-empty-heading`\n*  :ref:`axe-rule-heading-order`\n*  :ref:`axe-rule-page-has-heading-one`'
        }

        template_data = procedure.template_data(lang="ja")
        assert template_data == expected_template_data
