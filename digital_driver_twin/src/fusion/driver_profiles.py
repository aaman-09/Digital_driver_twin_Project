
import csv
from pathlib import Path
from datetime import datetime


# Project root: digital_driver_twin
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = PROJECT_ROOT / "data"
PROFILE_FILE = PROFILE_DIR / "driver_profiles.csv"

FIELDNAMES = ["driver_id", "name", "created_at", "notes"]


def ensure_profile_file():
    """Create the data folder and CSV file if they do not exist."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if not PROFILE_FILE.exists():
        with PROFILE_FILE.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()


def get_all_profiles():
    """Return all saved driver profiles."""
    ensure_profile_file()

    with PROFILE_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def create_driver_profile(name, notes=""):
    """Create and save a new driver profile."""
    name = name.strip()
    notes = notes.strip()

    if not name:
        return False, "Driver name cannot be empty."

    profiles = get_all_profiles()

    # Prevent duplicate driver names (case-insensitive).
    if any(p["name"].strip().casefold() == name.casefold()
           for p in profiles):
        return False, "A driver with this name already exists."

    # Generate a unique sequential driver ID.
    existing_numbers = []
    for profile in profiles:
        driver_id = profile.get("driver_id", "")
        if driver_id.startswith("DRV"):
            try:
                existing_numbers.append(int(driver_id[3:]))
            except ValueError:
                pass

    next_number = max(existing_numbers, default=0) + 1
    driver_id = f"DRV{next_number:03d}"

    new_profile = {
        "driver_id": driver_id,
        "name": name,
        "created_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "notes": notes,
    }

    with PROFILE_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writerow(new_profile)

    return True, f"Profile created successfully: {driver_id}"


if __name__ == "__main__":
    print("=== Digital Driver Twin: Driver Profiles ===")

    driver_name = input("Enter driver name: ")
    driver_notes = input("Notes (optional): ")

    success, message = create_driver_profile(
        driver_name, driver_notes
    )
    print(message)

    if success:
        print("\nSaved profiles:")
        for profile in get_all_profiles():
            print(
                f'{profile["driver_id"]} - {profile["name"]}'
            )
