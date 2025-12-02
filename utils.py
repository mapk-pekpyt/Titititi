def get_display_name(user):
    if user.username:
        return f"@{user.username}"
    if user.first_name:
        return user.first_name
    return str(user.id)