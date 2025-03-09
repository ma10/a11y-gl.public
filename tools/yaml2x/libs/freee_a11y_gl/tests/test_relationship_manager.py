import pytest
from freee_a11y_gl import setup_instances
from freee_a11y_gl.relationship_manager import RelationshipManager
from freee_a11y_gl.models.content import Category, Guideline
from freee_a11y_gl.models.check import Check
from freee_a11y_gl.models.faq.article import Faq
from freee_a11y_gl.models.faq.tag import FaqTag

def test_relationship_manager_initialization(setup_test_env):
    """Test RelationshipManager initialization."""
    rel_manager = setup_instances(str(setup_test_env))
    assert isinstance(rel_manager, RelationshipManager)

def test_guideline_check_relationships(setup_test_env):
    """Test relationships between guidelines and checks."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Get test guideline and its checks
    guideline = Guideline.get_by_id('gl-test')
    checks = guideline.checks
    
    # Verify bidirectional relationships
    for check in checks:
        assert guideline in check.guidelines
    
    # Verify specific relationships
    check_ids = {check.id for check in checks}
    assert check_ids == {'0001', '0002', '0003'}

def test_faq_relationships(setup_test_env):
    """Test FAQ relationships with guidelines, checks, and tags."""
    rel_manager = setup_instances(str(setup_test_env))
    
    faq = Faq.get_by_id('f0001')
    
    # Test FAQ-Tag relationships
    tag_ids = {tag.id for tag in faq.tags}
    assert tag_ids == {'markup', 'test_tag'}
    
    for tag in faq.tags:
        assert faq in tag.articles
    
    # Test FAQ-Guideline relationships
    guideline = next(gl for gl in faq.guidelines if gl.id == 'gl-test')
    assert guideline.id == 'gl-test'
    
    # Test FAQ-Check relationships
    check_ids = {check.id for check in faq.checks}
    assert check_ids == {'0001', '0002'}

def test_category_guideline_relationships(setup_test_env):
    """Test relationships between categories and guidelines."""
    rel_manager = setup_instances(str(setup_test_env))
    
    category = Category.get_by_id('dynamic_content')
    
    # Test that the category has the test guideline
    guideline_ids = {gl.id for gl in category.guidelines}
    assert 'gl-test' in guideline_ids
    
    # Test bidirectional relationship
    guideline = Guideline.get_by_id('gl-test')
    assert guideline.category == category

def test_wcag_relationships(setup_test_env):
    """Test WCAG success criteria relationships."""
    rel_manager = setup_instances(str(setup_test_env))
    
    guideline = Guideline.get_by_id('gl-test')
    
    # Test WCAG SC relationships
    sc_ids = {sc.id for sc in guideline.sc}
    assert sc_ids == {'1.1.1', 'test_sc'}
