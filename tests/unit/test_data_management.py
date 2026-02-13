import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel
from socialseed_e2e.test_data.factories import DataFactory
from socialseed_e2e.test_data.seeder import DataSeeder

class MockUser(BaseModel):
    username: str
    email: str
    is_active: bool = True

class UserFactory(DataFactory[MockUser]):
    model = MockUser
    
    def definition(self):
        return {
            "username": self.faker.user_name(),
            "email": self.faker.email()
        }

@pytest.fixture
def seeder():
    return DataSeeder()

@pytest.fixture
def user_factory():
    return UserFactory()

def test_factory_build(user_factory):
    user = user_factory.build()
    assert isinstance(user, MockUser)
    assert user.username
    assert user.email
    assert user.is_active is True

def test_factory_override(user_factory):
    user = user_factory.build(username="custom_user", is_active=False)
    assert user.username == "custom_user"
    assert user.is_active is False
    # Email should still be generated
    assert user.email

def test_factory_create_with_persist(user_factory):
    persist_mock = MagicMock(side_effect=lambda x: x)
    user = user_factory.create(persist_fn=persist_mock)
    
    persist_mock.assert_called_once()
    assert isinstance(user, MockUser)

def test_seeder_lifecycle(seeder, user_factory):
    seeder.register_factory("user", user_factory)
    
    persist_mock = MagicMock(side_effect=lambda x: x)
    cleanup_mock = MagicMock()
    
    # Test context manager cleanup
    with seeder.scope() as s:
        # Create 2 users
        users = s.seed("user", count=2, persist_fn=persist_mock, cleanup_fn=cleanup_mock)
        assert len(users) == 2
        assert cleanup_mock.call_count == 0 # Cleanup happens on exit
    
    # After exit, cleanup should have been called for each item
    assert cleanup_mock.call_count == 2
    # Verify calls with correct objects (LIFO order theoretically, but mock checks args)
    # LIFO: cleanup user2, then user1.
    
    # Verify objects passed to cleanup
    cleanup_mock.assert_any_call(users[0])
    cleanup_mock.assert_any_call(users[1])

def test_seeder_manual_cleanup(seeder, user_factory):
    cleanup_mock = MagicMock()
    # Manual seed
    seeder.seed(user_factory, count=1, cleanup_fn=cleanup_mock)
    
    assert cleanup_mock.call_count == 0
    seeder.cleanup()
    assert cleanup_mock.call_count == 1
