# 🎯 РУКОВОДСТВО ПО ПРИМЕНЕНИЮ ПРИНЦИПА DRY

## 📖 Что такое DRY?

**DRY (Don't Repeat Yourself)** - принцип разработки программного обеспечения, направленный на снижение дублирования кода. Вместо повторения одного и того же кода в разных местах, мы создаем абстракции, которые можно переиспользовать.

## 🔧 Применение DRY в SolarBalance

### 1. Декоратор `@with_db_session`

#### Проблема без DRY:
```python
# ❌ Повторяющийся код управления сессиями
async def get_user(self, telegram_id: int):
    async with self.get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def create_user(self, telegram_id: int, name: str):
    async with self.get_session() as session:
        user = User(telegram_id=telegram_id, name=name)
        session.add(user)
        await session.commit()
        return user

async def update_user(self, telegram_id: int, name: str):
    async with self.get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.name = name
            await session.commit()
        return user
```

#### Решение с DRY:
```python
# ✅ Использование декоратора
@with_db_session
async def get_user(self, telegram_id: int):
    result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

@with_db_session
async def create_user(self, telegram_id: int, name: str):
    user = User(telegram_id=telegram_id, name=name)
    self._session.add(user)
    await self._session.flush()
    return user

@with_db_session
async def update_user(self, telegram_id: int, name: str):
    result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        user.name = name
        await self._session.flush()
    return user
```

### 2. Контекстный менеджер `db_session_context`

#### Для сложных операций:
```python
# ✅ Использование контекстного менеджера
async def complex_operation(self, user_id: int):
    async with db_session_context(self.db_manager) as session:
        # Множественные операции в одной транзакции
        user = await session.get(User, user_id)
        user.last_activity = datetime.utcnow()
        
        # Создание связанных записей
        chart = NatalChart(user_id=user.id, ...)
        session.add(chart)
        
        # Все изменения будут зафиксированы автоматически
        await session.flush()
        return user, chart
```

## 🚀 Преимущества применения DRY

### 1. **Меньше кода**
- Устранение дублирования
- Более компактные методы
- Легче читать и понимать

### 2. **Централизованное управление**
- Единая логика работы с сессиями
- Автоматическая обработка ошибок
- Консистентное поведение

### 3. **Безопасность**
- Автоматический rollback при ошибках
- Правильное закрытие соединений
- Защита от утечек ресурсов

### 4. **Производительность**
- Оптимизированное управление пулом соединений
- Меньше накладных расходов
- Лучшая масштабируемость

## 📋 Лучшие практики

### 1. **Когда использовать декоратор:**
- Простые CRUD операции
- Одиночные запросы к БД
- Методы, которые не требуют сложной логики

### 2. **Когда использовать контекстный менеджер:**
- Сложные транзакции
- Множественные операции в одной сессии
- Когда нужен явный контроль над сессией

### 3. **Структура методов с декоратором:**
```python
@with_db_session
async def method_name(self, param1: type, param2: type) -> ReturnType:
    """
    Краткое описание метода.
    
    Args:
        param1: описание параметра
        param2: описание параметра
        
    Returns:
        описание возвращаемого значения
    """
    # Логика метода
    result = await self._session.execute(...)
    return result.scalar_one_or_none()
```

## 🔍 Примеры из реального кода

### Сервис пользователей:
```python
class UserService:
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db_manager = db_manager
    
    @with_db_session
    async def get_or_create_user(self, telegram_id: int, name: str) -> Tuple[User, bool]:
        """Получить или создать пользователя"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user, False
        
        user = User(telegram_id=telegram_id, name=name)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user, True
    
    @with_db_session
    async def update_profile(self, telegram_id: int, **kwargs) -> Optional[User]:
        """Обновить профиль пользователя"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self._session.flush()
        await self._session.refresh(user)
        return user
```

### Сервис натальных карт:
```python
class ChartService:
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db_manager = db_manager
    
    @with_db_session
    async def create_chart(self, telegram_id: int, chart_data: dict) -> NatalChart:
        """Создать натальную карту"""
        chart = NatalChart(telegram_id=telegram_id, **chart_data)
        self._session.add(chart)
        await self._session.flush()
        await self._session.refresh(chart)
        return chart
    
    @with_db_session
    async def get_user_charts(self, telegram_id: int) -> List[NatalChart]:
        """Получить все карты пользователя"""
        result = await self._session.execute(
            select(NatalChart)
            .where(NatalChart.telegram_id == telegram_id)
            .order_by(NatalChart.created_at.desc())
        )
        return list(result.scalars().all())
```

## ⚠️ Важные моменты

### 1. **Обработка ошибок:**
```python
@with_db_session
async def safe_operation(self, user_id: int):
    try:
        result = await self._session.execute(...)
        return result.scalar_one_or_none()
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка в safe_operation: {e}")
        # Декоратор автоматически выполнит rollback
        raise
```

### 2. **Транзакции:**
```python
@with_db_session
async def transactional_operation(self, user_id: int):
    # Все операции в этом методе будут в одной транзакции
    user = await self._session.get(User, user_id)
    user.last_activity = datetime.utcnow()
    
    chart = NatalChart(user_id=user.id, ...)
    self._session.add(chart)
    
    # Если что-то пойдет не так, все изменения откатятся
    await self._session.flush()
    return user, chart
```

### 3. **Производительность:**
```python
# ✅ Хорошо - один запрос
@with_db_session
async def get_user_with_charts(self, telegram_id: int):
    result = await self._session.execute(
        select(User)
        .options(selectinload(User.natal_charts))
        .where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()

# ❌ Плохо - N+1 проблема
@with_db_session
async def get_user_with_charts_bad(self, telegram_id: int):
    user = await self._session.get(User, telegram_id)
    # Это вызовет дополнительные запросы
    charts = user.natal_charts  # N+1 проблема!
    return user
```

## 🎯 Заключение

Применение принципа DRY в SolarBalance через декоратор `@with_db_session` и контекстный менеджер `db_session_context` позволяет:

1. **Уменьшить количество кода** на 30-50%
2. **Повысить читаемость** и поддерживаемость
3. **Обеспечить безопасность** работы с БД
4. **Улучшить производительность** за счет оптимизации
5. **Стандартизировать** подход к работе с данными

Используйте эти инструменты для создания чистого, эффективного и масштабируемого кода! 🚀 