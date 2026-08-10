FOUNDING_ADMIN_LIMIT = 3


def apply_founding_admin(user_data, existing_user_count):
    if existing_user_count < FOUNDING_ADMIN_LIMIT:
        return {
            **user_data,
            'role': 'admin',
            'email_verified': True,
        }
    return user_data
