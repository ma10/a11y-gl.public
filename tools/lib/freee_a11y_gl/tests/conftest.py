import yaml
import json
import pytest
import shutil
from pathlib import Path
from freee_a11y_gl.models.content import Guideline, Category
from freee_a11y_gl.models.check import Check, CheckTool
from freee_a11y_gl.models.faq.article import Faq
from freee_a11y_gl.models.faq.tag import FaqTag
from freee_a11y_gl.models.reference import WcagSc
from freee_a11y_gl.constants import CHECK_TOOLS
from freee_a11y_gl.relationship_manager import RelationshipManager

SAMPLES_DIR = Path(__file__).parent / "sample_files"

@pytest.fixture(scope="session")
def sample_dir(tmp_path_factory):
    """
    既存のサンプルファイル群を一時ディレクトリにコピーするフィクスチャ。
    テストセッション終了後、一時ディレクトリごと削除される。
    """
    # 一時ディレクトリを作成
    temp_dir = tmp_path_factory.mktemp("samples")
    
    # 既存のサンプルファイル群を一時ディレクトリにコピー
    shutil.copytree(SAMPLES_DIR, temp_dir, dirs_exist_ok=True)
    
    yield temp_dir
    
    # テスト終了後に一時ディレクトリ全体を削除
    shutil.rmtree(temp_dir)

@pytest.fixture(autouse=True)
def reset_instances():
    """
    Clear all instances before and after each test.
    """

    # Clear all instances before the test
    Check._instances.clear()
    CheckTool._instances.clear()
    Guideline._instances.clear()
    WcagSc._instances.clear()
    Category._instances.clear()
    Faq._instances.clear()
    FaqTag._instances.clear()
    RelationshipManager.reset()
    # InfoRef._instances.clear()
    # AxeRule._instances.clear()

    yield
    
    # Clear all instances after the test
    Check._instances.clear()
    CheckTool._instances.clear()  # Clear existing CheckTool instances
    Guideline._instances.clear()
    WcagSc._instances.clear()
    Category._instances.clear()
    Faq._instances.clear()
    FaqTag._instances.clear()
    RelationshipManager.reset()

@pytest.fixture
def check_tools():
    """
    Set up check tools for tests.
    This fixture is used to set up any necessary check tools before running tests.
    """
    for tool_id, tool_names in CHECK_TOOLS.items():
        CheckTool(tool_id, tool_names)
    yield CheckTool

@pytest.fixture
def all_check_data(sample_dir, check_factory):
    """
    Load all check data from YAML files in the sample directory.
    """
    sample_check_dir = sample_dir / "data/yaml/checks"
    check_files = sample_check_dir.rglob("*.yaml")
    file_list = [str(file.relative_to(sample_check_dir).with_suffix('')) for file in check_files]
    for file in file_list:
        check = check_factory(file)
    yield Check

@pytest.fixture
def check_factory(sample_dir, check_tools):
    """
    Factory function to create Check instances from YAML files.
    """
    def _create_check(sample_check_path):
        sample_check_file = sample_dir / f"data/yaml/checks/{sample_check_path}.yaml"
        with open(sample_check_file, "r", encoding="utf-8") as file:
            check_data = yaml.safe_load(file)
        check_data["src_path"] = sample_check_file
        return Check(check_data)
    
    yield _create_check

@pytest.fixture
def all_guideline_data(sample_dir, guideline_factory):
    """
    Load all guideline data from YAML files in the sample directory.
    """
    sample_guideline_dir = sample_dir / "data/yaml/gl"
    guideline_files = sample_guideline_dir.rglob("*.yaml")
    file_list = [str(file.relative_to(sample_guideline_dir).with_suffix('')) for file in guideline_files]
    for file in file_list:
        guideline = guideline_factory(file)
    yield Guideline

@pytest.fixture
def guideline_factory(sample_dir, all_check_data, setup_categories, setup_wcag_sc):
    """
    Factory function to create Guideline instances from YAML files.
    """
    def _create_guideline(sample_guideline_path):
        sample_guideline_file = sample_dir / f"data/yaml/gl/{sample_guideline_path}.yaml"
        with open(sample_guideline_file, "r", encoding="utf-8") as file:
            guideline_data = yaml.safe_load(file)
        guideline_data["src_path"] = sample_guideline_file
        return Guideline(guideline_data)
    
    yield _create_guideline

@pytest.fixture
def faq_factory(sample_dir, all_guideline_data, setup_faq_tags):
    """
    Factory function to create Faq instances from YAML files.
    """
    def _create_faq(sample_faq_path):
        sample_faq_file = sample_dir / f"data/yaml/faq/{sample_faq_path}.yaml"
        with open(sample_faq_file, "r", encoding="utf-8") as file:
            faq_data = yaml.safe_load(file)
        faq_data["src_path"] = sample_faq_file
        return Faq(faq_data)
    
    yield _create_faq

@pytest.fixture
def setup_categories(sample_dir):
    """
    Set up categories for tests.
    This fixture is used to set up any necessary categories before running tests.
    """
    sample_category_file = sample_dir / "data/json/guideline-categories.json"
    with open(sample_category_file, "r", encoding="utf-8") as file:
        category_data = json.load(file)
    for key, data in category_data.items():
        Category(key, data)
    yield Category

@pytest.fixture
def setup_wcag_sc(sample_dir):
    """
    Set up WCAG success criteria for tests.
    This fixture is used to set up any necessary WCAG success criteria before running tests.
    """
    sample_wcag_sc_file = sample_dir / "data/json/wcag-sc.json"
    with open(sample_wcag_sc_file, "r", encoding="utf-8") as file:
        wcag_sc_data = json.load(file)
    for key, data in wcag_sc_data.items():
        WcagSc(key, data)
    yield WcagSc

@pytest.fixture
def setup_faq_tags(sample_dir):
    """
    Set up FAQ tags for tests.
    This fixture is used to set up any necessary FAQ tags before running tests.
    """
    sample_faq_tags_file = sample_dir / "data/json/faq-tags.json"
    with open(sample_faq_tags_file, "r", encoding="utf-8") as file:
        tag_data = json.load(file)
    for key, data in tag_data.items():
        FaqTag(key, data)
    yield FaqTag
