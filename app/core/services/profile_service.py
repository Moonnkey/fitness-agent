from app.core.db.session import session_scope
from app.core.models.profile import UserProfile
from app.core.schemas.profile import UserProfileInput, UserProfileOutput

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def _calculate_bmr(input_data: UserProfileInput) -> int | None:
    if (
        input_data.height_cm is None
        or input_data.weight_kg is None
        or input_data.age is None
        or input_data.sex is None
    ):
        return None

    if input_data.sex == "male":
        value = 10 * input_data.weight_kg + 6.25 * input_data.height_cm - 5 * input_data.age + 5
    else:
        value = 10 * input_data.weight_kg + 6.25 * input_data.height_cm - 5 * input_data.age - 161
    return round(value)


def _calculate_tdee(input_data: UserProfileInput, bmr: int | None) -> int | None:
    if bmr is None or input_data.activity_level is None:
        return None
    return round(bmr * ACTIVITY_FACTORS[input_data.activity_level])


def _calculate_target_calories(input_data: UserProfileInput, tdee: int | None) -> int | None:
    if input_data.target_calories is not None:
        return round(input_data.target_calories)
    if tdee is None:
        return None
    if input_data.goal_type == "fat_loss":
        return max(round(tdee - 450), 1200)
    if input_data.goal_type == "muscle_gain":
        return round(tdee + 250)
    return tdee


def _calculate_target_protein(input_data: UserProfileInput) -> int | None:
    if input_data.target_protein_g is not None:
        return round(input_data.target_protein_g)
    if input_data.weight_kg is None:
        return None
    return round(input_data.weight_kg * 1.8)


def _to_output(profile: UserProfile) -> UserProfileOutput:
    input_data = UserProfileInput.model_validate(profile, from_attributes=True)
    bmr = _calculate_bmr(input_data)
    tdee = _calculate_tdee(input_data, bmr)
    return UserProfileOutput(
        id=profile.id,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal_type=profile.goal_type,
        goal_weight_kg=profile.goal_weight_kg,
        target_calories=profile.target_calories,
        target_protein_g=profile.target_protein_g,
        bmr=bmr,
        tdee=tdee,
        calculated_target_calories=_calculate_target_calories(input_data, tdee),
        calculated_target_protein_g=_calculate_target_protein(input_data),
    )


def get_user_profile() -> UserProfileOutput | None:
    with session_scope() as session:
        profile = session.get(UserProfile, 1)
        if profile is None:
            return None
        return _to_output(profile)


def update_user_profile(input_data: UserProfileInput) -> UserProfileOutput:
    with session_scope() as session:
        profile = session.get(UserProfile, 1)
        if profile is None:
            profile = UserProfile(id=1)
            session.add(profile)

        for field, value in input_data.model_dump().items():
            setattr(profile, field, value)

        session.flush()
        return _to_output(profile)
