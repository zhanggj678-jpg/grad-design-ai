"""认证服务单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.auth_service import hash_password, verify_password, AuthService

def test_password_hash():
    """测试密码哈希和验证"""
    hashed = hash_password("test123")
    assert hashed != "test123"
    assert verify_password("test123", hashed) == True
    assert verify_password("wrong", hashed) == False

def test_register_validation():
    """测试注册验证"""
    # 用户名太短
    result = AuthService.register("ab", "test@test.com", "123456")
    assert result["success"] == False
    assert "用户名" in result["error"]

    # 密码太短
    result = AuthService.register("testuser", "test@test.com", "123")
    assert result["success"] == False
    assert "密码" in result["error"]

    # 邮箱格式错误
    result = AuthService.register("testuser", "notanemail", "123456")
    assert result["success"] == False
    assert "邮箱" in result["error"]

if __name__ == "__main__":
    test_password_hash()
    test_register_validation()
    print("All auth tests passed!")
