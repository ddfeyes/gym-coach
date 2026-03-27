"""
Basic pytest tests for gym-coach models and routes.
Run with: pytest tests/ -v
"""
import os
import sys
import pytest
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use a test database
TEST_DB = tempfile.mktemp(suffix='.db')


@pytest.fixture(scope='module')
def app():
    """Create test Flask app with test database."""
    os.environ['TESTING'] = '1'

    # Create test database with schema
    from database import create_tables, get_db
    create_tables()

    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestNutritionModel:
    """Tests for nutrition model."""

    def test_log_meal(self):
        """Test logging a meal."""
        from models.user import create_user
        from models.nutrition import log_meal

        user_id = create_user(
            telegram_id=99999,
            name='Test User',
            gender='male',
            age=25,
            height_cm=180,
            weight_kg=75,
            experience_level='beginner',
            training_days_per_week=3,
            primary_goal='muscle_gain',
        )

        log_id = log_meal(user_id, 'Test lunch', 'lunch', 500, 40, 50, 20)
        assert log_id is not None
        assert log_id > 0


class TestWeightLog:
    """Tests for weight log model."""

    def test_log_weight(self):
        """Test logging weight."""
        from models.user import create_user
        from models.weight_log import log_weight, get_latest_weight

        user_id = create_user(
            telegram_id=99998,
            name='Test User 2',
            gender='female',
            age=30,
            height_cm=165,
            weight_kg=60,
            experience_level='intermediate',
            training_days_per_week=4,
            primary_goal='fat_loss',
        )

        log_id = log_weight(user_id, 59.5)
        assert log_id is not None

        latest = get_latest_weight(user_id)
        assert latest is not None
        assert latest['weight_kg'] == 59.5


class TestSleepLog:
    """Tests for sleep log model."""

    def test_log_sleep(self):
        """Test logging sleep."""
        from models.user import create_user
        from models.sleep_log import log_sleep, get_sleep_summary

        user_id = create_user(
            telegram_id=99997,
            name='Test User 3',
            gender='male',
            age=28,
            height_cm=185,
            weight_kg=85,
            experience_level='advanced',
            training_days_per_week=5,
            primary_goal='strength',
        )

        log_id = log_sleep(user_id, 7.5, quality=4)
        assert log_id is not None

        summary = get_sleep_summary(user_id, days=1)
        assert summary['average_hours'] == 7.5
        assert summary['average_quality'] == 4.0


class TestUserModel:
    """Tests for user model."""

    def test_create_and_get_user(self):
        """Test creating and retrieving a user."""
        from models.user import create_user, get_user_by_telegram_id

        user_id = create_user(
            telegram_id=99996,
            name='Test User 4',
            gender='male',
            age=35,
            height_cm=175,
            weight_kg=70,
            experience_level='beginner',
            training_days_per_week=3,
            primary_goal='health',
        )

        assert user_id is not None
        user = get_user_by_telegram_id(99996)
        assert user is not None
        assert user['name'] == 'Test User 4'
        assert user['onboarding_completed'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
