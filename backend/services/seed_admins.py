from models import db
from models.models import MembershipStatus, User
from app import app


# ── Team Member Admin Accounts ─────────────────────────────────────────────────
# Add or remove team members here as needed.
# Passwords should be changed by each member after first login.

ADMIN_USERS = [
    {
        "username": "adamknell",
        "email_address": "ajknell@syr.edu",
        "first_name": "Adam",
        "last_name": "Knell",
        "membership_status":MembershipStatus.ADMIN,
        "password": "password",
    },
    {
        "username": "zachgrande",
        "email_address": "zmgrande@syr.edu",
        "first_name": "Zach",
        "last_name": "Grande",
        "membership_status":MembershipStatus.ADMIN,
        "password": "password!",
    },
    {
        "username": "katiesucks",
        "email_address": "kfmatula@syr.edu",
        "first_name": "Katie",
        "last_name": "Matulac",
        "membership_status":MembershipStatus.ADMIN,
        "password": "password!",
    },
    {
        "username": "adonyarko",
        "email_address": "anyarko@syr.edu",
        "first_name": "Adomako",
        "last_name": "Nyarko",
        "membership_status":MembershipStatus.ADMIN,
        "password": "password!",
    },
    {
        "username": "joewac",
        "email_address": "jwac@syr.edu",
        "first_name": "Joe",
        "last_name": "Wac",
        "membership_status":MembershipStatus.FREE,
        "password": "password!",
    },
]


def seed_admins():
    seeded = 0
    skipped = 0

    for member in ADMIN_USERS:
        # Check if user already exists to keep the script idempotent
        existing = User.query.filter(
            (User.username == member["username"]) |
            (User.email == member["email_address"])
        ).first()

        if existing:
            print(f"[SKIP]  '{member['username']}' already exists — skipping.")
            skipped += 1
            continue

        new_user = User(
            username=member["username"],
            email=member["email_address"],
            first_name=member["first_name"],
            last_name=member["last_name"],
            membership_status=member["membership_status"],
            password_hash=member["password"], # Store plaintext for now; should be changed on first login
            #password_hash=generate_password_hash(member["password"]),
        )

        db.session.add(new_user)
        print(f"[ADD]   '{member['username']}' added as admin.")
        seeded += 1

    db.session.commit()
    print(f"\nDone. {seeded} admin(s) seeded, {skipped} skipped.")


if __name__ == "__main__":
    with app.app_context():
        seed_admins()