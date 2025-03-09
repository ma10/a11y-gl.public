import pytest
from freee_a11y_gl.models.check import Check, CheckTool
from freee_a11y_gl import setup_instances

def test_check_creation(setup_test_env):
    """Test check creation and basic properties."""
    rel_manager = setup_instances(str(setup_test_env))
    
    # Test getting all checks
    checks = Check.get_all()
    assert len(checks) >= 3  # At least our test checks
    
    # Test getting specific check
    test_check = Check.get_by_id('0001')
    assert test_check.id == '0001'
    assert test_check.check.ja == 'コードテストチェック項目'
    assert test_check.check.en == 'Code test check item'
    assert test_check.severity == 'normal'
    assert test_check.target == 'code'
    assert 'web' in test_check.platform

def test_check_implementations(setup_test_env):
    """Test check implementations for code checks."""
    rel_manager = setup_instances(str(setup_test_env))
    
    code_check = Check.get_by_id('0001')
    assert hasattr(code_check, 'implementations')
    assert len(code_check.implementations) == 1
    
    impl = code_check.implementations[0]
    assert impl.title.ja == '実装例1'
    assert len(impl.methods) == 2
    assert all(method.platform == 'web' for method in impl.methods)

def test_check_conditions(setup_test_env):
    """Test check conditions for product checks."""
    rel_manager = setup_instances(str(setup_test_env))
    
    product_check = Check.get_by_id('0003')
    assert hasattr(product_check, 'conditions')
    assert len(product_check.conditions) == 2
    
    # Test web condition
    web_condition = [c for c in product_check.conditions if c.platform == 'web'][0]
    assert web_condition.type == 'simple'
    assert web_condition.id == '0003-web-test'
    
    # Test mobile conditions
    mobile_condition = [c for c in product_check.conditions if c.platform == 'mobile'][0]
    assert mobile_condition.type == 'and'
    assert len(mobile_condition.conditions) == 2
    assert {c.id for c in mobile_condition.conditions} == {'0003-ios-test', '0003-android-test'}

def test_check_relationships(setup_test_env):
    """Test check relationships with guidelines."""
    rel_manager = setup_instances(str(setup_test_env))
    
    check = Check.get_by_id('0001')
    
    # Test guideline relationships
    assert len(check.guidelines) >= 1
    gl = next(gl for gl in check.guidelines if gl.id == 'gl-test')
    assert gl.id == 'gl-test'

def test_invalid_check_data():
    """Test check validation for invalid data."""
    with pytest.raises(ValueError):
        Check({
            'id': 'invalid',  # Invalid format
            'check': {'ja': 'テスト', 'en': 'Test'},
            'severity': 'normal',
            'target': 'code',
            'platform': ['web']
        })
    
    with pytest.raises(ValueError):
        Check({
            'id': '0001',
            'check': {'ja': 'テスト'},  # Missing 'en'
            'severity': 'normal',
            'target': 'code',
            'platform': ['web']
        })
    
    with pytest.raises(ValueError):
        Check({
            'id': '0001',
            'check': {'ja': 'テスト', 'en': 'Test'},
            'severity': 'unknown',  # Invalid severity
            'target': 'code',
            'platform': ['web']
        })
