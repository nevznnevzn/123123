import pytest

from database import DatabaseManager


# Фикстура для создания чистой базы данных для каждого теста
@pytest.fixture
def db_manager():
    """Создает экземпляр DatabaseManager с базой данных в памяти."""
    manager = DatabaseManager(database_url="sqlite:///:memory:")
    # Base.metadata.create_all(manager.engine) # таблицы создаются в __init__
    return manager


def test_user_creation_default_notifications(db_manager: DatabaseManager):
    """Тест: при создании пользователя уведомления должны быть включены по умолчанию."""
    user, created = db_manager.get_or_create_user(telegram_id=1, name="John Doe")
    assert created is True
    assert user.notifications_enabled is True


def test_set_notifications(db_manager: DatabaseManager):
    """Тест: функция set_notifications корректно меняет флаг в базе."""
    # 1. Создаем пользователя
    telegram_id = 123
    db_manager.get_or_create_user(telegram_id=telegram_id, name="Tester")

    # 2. Проверяем, что по умолчанию уведомления включены
    user_profile = db_manager.get_user_profile(telegram_id)
    assert user_profile.notifications_enabled is True

    # 3. Выключаем уведомления
    result_off = db_manager.set_notifications(telegram_id, False)
    assert result_off is True
    updated_user_profile_off = db_manager.get_user_profile(telegram_id)
    assert updated_user_profile_off.notifications_enabled is False

    # 4. Включаем уведомления обратно
    result_on = db_manager.set_notifications(telegram_id, True)
    assert result_on is True
    updated_user_profile_on = db_manager.get_user_profile(telegram_id)
    assert updated_user_profile_on.notifications_enabled is True


def test_get_users_for_mailing(db_manager: DatabaseManager):
    """Тест: функция get_users_for_mailing возвращает правильных пользователей."""
    # 1. Создаем пользователей с разными статусами уведомлений
    db_manager.get_or_create_user(
        telegram_id=1, name="User One"
    )  # Уведомления включены
    db_manager.get_or_create_user(
        telegram_id=2, name="User Two"
    )  # Уведомления включены
    db_manager.get_or_create_user(telegram_id=3, name="User Three")
    db_manager.set_notifications(telegram_id=3, enabled=False)  # Выключаем уведомления
    db_manager.get_or_create_user(
        telegram_id=4, name="User Four"
    )  # Уведомления включены

    # 2. Получаем список для рассылки
    mailing_list = db_manager.get_users_for_mailing()

    # 3. Проверяем результат
    assert len(mailing_list) == 3
    mailing_ids = {user.telegram_id for user in mailing_list}
    assert mailing_ids == {1, 2, 4}
    assert 3 not in mailing_ids
