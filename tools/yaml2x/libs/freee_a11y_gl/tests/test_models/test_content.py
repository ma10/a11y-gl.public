import pytest
from freee_a11y_gl.models.content import Category, Guideline
from freee_a11y_gl import setup_instances

def test_category_creation(setup_test_env):
    """Test category creation and basic properties."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Test getting all categories
    categories = Category.get_all()
    assert len(categories) >= 2  # dynamic_content and test_category
    
    # Test getting specific category
    dynamic_content = Category.get_by_id('dynamic_content')
    assert dynamic_content.id == 'dynamic_content'
    assert dynamic_content.title.ja == '動的コンテンツ'
    assert dynamic_content.title.en == 'Dynamic Content'
    assert dynamic_content.description.ja == '動的なコンテンツに関するガイドライン'

def test_guideline_creation(setup_test_env):
    """Test guideline creation and basic properties."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Test getting all guidelines
    guidelines = Guideline.get_all()
    assert len(guidelines) >= 1  # At least test.yaml
    
    # Test getting specific guideline
    test_gl = Guideline.get_by_id('gl-test')
    assert test_gl.id == 'gl-test'
    assert test_gl.title.ja == 'テストガイドライン'
    assert test_gl.title.en == 'Test Guideline'
    assert len(test_gl.checks) == 3
    assert len(test_gl.sc) == 2

def test_guideline_relationships(setup_test_env):
    """Test guideline relationships with other entities."""
    rel_manager = setup_instances(str(setup_test_env))
    
    test_gl = Guideline.get_by_id('gl-test')
    
    # Test category relationship
    assert test_gl.category.id == 'dynamic_content'
    
    # Test check relationships
    check_ids = {check.id for check in test_gl.checks}
    assert check_ids == {'0001', '0002', '0003'}
    
    # Test WCAG SC relationships
    sc_ids = {sc.id for sc in test_gl.sc}
    assert sc_ids == {'1.1.1', 'test_sc'}

def test_invalid_guideline_data():
    """Test guideline validation for invalid data."""
    with pytest.raises(ValueError):
        Guideline({
            'id': 'invalid-gl',
            # Missing required fields
        })

    with pytest.raises(ValueError):
        Guideline({
            'id': 'invalid-gl',
            'title': {'ja': 'テスト'},  # Missing 'en'
            'category': 'nonexistent',
            'platform': ['web']
        })
