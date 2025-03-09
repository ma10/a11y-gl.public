import pytest
from freee_a11y_gl.models.faq.article import Faq
from freee_a11y_gl.models.faq.tag import FaqTag
from freee_a11y_gl import setup_instances
from datetime import datetime

def test_faq_tag_creation(setup_test_env):
    """Test FAQ tag creation and basic properties."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Test getting all tags
    tags = FaqTag.get_all()
    assert len(tags) >= 2  # At least markup and test_tag
    
    # Test getting specific tag
    markup_tag = FaqTag.get_by_id('markup')
    assert markup_tag.id == 'markup'
    assert markup_tag.title.ja == 'マークアップ'
    assert markup_tag.title.en == 'Markup'
    assert markup_tag.description.ja == 'HTMLマークアップに関する質問'

def test_faq_creation(setup_test_env):
    """Test FAQ creation and basic properties."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Test getting all FAQs
    faqs = Faq.get_all()
    assert len(faqs) >= 1  # At least our test FAQ
    
    # Test getting specific FAQ
    test_faq = Faq.get_by_id('f0001')
    assert test_faq.id == 'f0001'
    assert test_faq.title.ja == 'テストFAQ'
    assert test_faq.title.en == 'Test FAQ'
    assert test_faq.updated == '2024-03-09'
    assert len(test_faq.tags) == 2

def test_faq_relationships(setup_test_env):
    """Test FAQ relationships with other entities."""
    rel_manager = setup_instances(str(setup_test_env))
    
    faq = Faq.get_by_id('f0001')
    
    # Test tag relationships
    tag_ids = {tag.id for tag in faq.tags}
    assert tag_ids == {'markup', 'test_tag'}
    
    # Test guideline relationships
    gl_ids = {gl.id for gl in faq.guidelines}
    assert gl_ids == {'gl-test'}
    
    # Test check relationships
    check_ids = {check.id for check in faq.checks}
    assert check_ids == {'0001', '0002'}

def test_faq_tag_relationships(setup_test_env):
    """Test FAQ tag relationships."""
    rel_manager = setup_instances(str(setup_test_env))
    
    markup_tag = FaqTag.get_by_id('markup')
    
    # Test articles relationship
    assert len(markup_tag.articles) >= 1
    assert any(article.id == 'f0001' for article in markup_tag.articles)

def test_invalid_faq_data():
    """Test FAQ validation for invalid data."""
    with pytest.raises(ValueError):
        Faq({
            'id': 'invalid',
            # Missing required fields
        })
    
    with pytest.raises(ValueError):
        Faq({
            'id': 'f0001',
            'sortKey': 10000,
            'title': {'ja': 'テスト'},  # Missing 'en'
            'updated': '2024-03-09',
            'tags': ['nonexistent_tag']
        })

    with pytest.raises(ValueError):
        Faq({
            'id': 'f0001',
            'sortKey': 10000,
            'title': {'ja': 'テスト', 'en': 'Test'},
            'updated': 'invalid-date',  # Invalid date format
            'tags': ['markup']
        })
