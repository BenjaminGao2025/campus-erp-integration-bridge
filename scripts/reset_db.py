from app.db import reset_database
from scripts.seed_demo_data import seed_demo_data


if __name__ == "__main__":
    reset_database()
    seed_demo_data()
    print("Reset database and seeded synthetic demo data.")
