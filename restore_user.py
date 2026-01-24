from werkzeug.security import generate_password_hash
from db_wrapper import save_users, load_users

print("Loading users...")
users = load_users()

# Check if 'admin' is the placeholder dict
if 'admin' in users and len(users) == 1:
    # It might be the default dict if DB is empty.
    # We want to persist the default admin too if we are saving.
    pass

print("Creating user 'pavel'...")
users['pavel'] = {
    'password': generate_password_hash('madle'),
    'name': 'Pavel',
    'role': 'admin'
}

print("Saving to database...")
save_users(users)
print("Done. User 'pavel' (password 'madle') restored.")
