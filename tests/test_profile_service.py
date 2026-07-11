from app.core.db.session import init_db
from app.core.schemas.profile import UserProfileInput
from app.core.services.profile_service import get_user_profile, update_user_profile


def test_update_user_profile_creates_and_updates_single_profile() -> None:
    init_db()

    created = update_user_profile(
        UserProfileInput(
            height_cm=175,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            goal_weight_kg=72,
        )
    )
    updated = update_user_profile(
        UserProfileInput(
            height_cm=175,
            weight_kg=78,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            goal_weight_kg=72,
            target_calories=2100,
            target_protein_g=150,
        )
    )

    assert created.id == updated.id
    assert updated.weight_kg == 78
    assert updated.target_calories == 2100
    assert updated.target_protein_g == 150


def test_get_user_profile_returns_none_when_missing() -> None:
    init_db()

    assert get_user_profile() is None


def test_profile_calculates_bmr_tdee_and_default_targets() -> None:
    init_db()

    profile = update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
        )
    )

    assert profile.bmr is not None
    assert profile.tdee is not None
    assert profile.calculated_target_calories is not None
    assert profile.calculated_target_protein_g == 144
    assert profile.bmr == 1780
    assert profile.tdee == 2759
    assert profile.calculated_target_calories == 2309
