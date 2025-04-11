import pytest
from freee_a11y_gl.models.check import CheckTool, Example, Procedure

class TestCheckTool:
    def test_init(self):
        """Test initialization of CheckTool."""
        tool = CheckTool(tool_id="axe", names={"ja": "アックス", "en": "Axe"})
        assert tool.id == "axe"
        assert tool.names["ja"] == "アックス"
        assert tool.names["en"] == "Axe"
        assert tool.examples == []
        assert CheckTool.get_by_id("axe") == tool

    def test_add_example(self, check_tools, check_factory):
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0].conditions[1].conditions[0]
        procedure = condition.procedure
        tool_name = procedure.tool.id
        tool = check_tools.get_by_id(tool_name)
        tool.examples.clear()  # Clear existing examples
        example = Example(procedure=procedure, check=sample_check)
        tool.add_example(example)
        assert len(tool.examples) == 1
        assert tool.examples[0] == example

    def test_get_name(self):
        """Test retrieving localized names."""
        tool = CheckTool(tool_id="axe", names={"ja": "アックス", "en": "Axe"})
        assert tool.get_name("ja") == "アックス"
        assert tool.get_name("en") == "Axe"
        assert tool.get_name("fr") == "アックス"  # Fallback to Japanese

    def test_list_all_and_list_all_ids(self):
        """Test listing all CheckTool instances and their IDs."""
        # Clear existing tools for testing
        CheckTool._instances.clear()
        tool1 = CheckTool(tool_id="axe", names={"ja": "アックス", "en": "Axe"})
        tool2 = CheckTool(tool_id="wave", names={"ja": "ウェーブ", "en": "Wave"})
        all_tools = CheckTool.list_all()
        all_ids = CheckTool.list_all_ids()
        assert len(all_tools) == 2
        assert tool1 in all_tools
        assert tool2 in all_tools
        assert "axe" in all_ids
        assert "wave" in all_ids

    def test_get_by_id(self):
        """Test retrieving a CheckTool by its ID."""
        tool = CheckTool(tool_id="axe", names={"ja": "アックス", "en": "Axe"})
        retrieved_tool = CheckTool.get_by_id("axe")
        assert retrieved_tool == tool
        assert CheckTool.get_by_id("nonexistent") is None

    def test_example_template_data(self, check_tools, check_factory):
        """Test generating example template data."""
        sample_check = check_factory("product/0561")
        condition = sample_check.conditions[0].conditions[1].conditions[0]
        procedure = condition.procedure
        tool_name = procedure.tool.id
        tool = check_tools.get_by_id(tool_name)
        example = Example(procedure=procedure, check=sample_check)
        template_data = example.template_data("ja")
        expected_template_data = {
            "id": example.procedure.id,
            "tool": tool_name,
            "tool_display_name": tool.get_name("ja"),
            "procedure": example.procedure.procedure['ja'],
            "check_id": sample_check.id,
            "check_text": sample_check.check_text['ja']
        }
        assert template_data == expected_template_data
