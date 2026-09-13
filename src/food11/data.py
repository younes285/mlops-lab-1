from pathlib import Path
from PIL import Image
import shutil

RAW_DIR = Path("data/food11_raw")
PROCESSED_DIR = Path("data/food11_processed")
MINI_DIR = Path("data/food11_processed_mini")

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100

CATEGORIES = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit",
}


def get_category(filename: str):
    category_id = filename.split("_")[0]
    return CATEGORIES.get(category_id)


def prepare_directories():
    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    if MINI_DIR.exists():
        shutil.rmtree(MINI_DIR)

    for split in ["training", "evaluation", "validation"]:
        for category in CATEGORIES.values():
            (PROCESSED_DIR / split / category).mkdir(parents=True, exist_ok=True)
            (MINI_DIR / split / category).mkdir(parents=True, exist_ok=True)


def process_dataset():
    for split in ["training", "evaluation", "validation"]:
        input_folder = RAW_DIR / split

        mini_counts = {
            category: 0
            for category in CATEGORIES.values()
        }

        print(f"Processing {split}...")

        for image_path in input_folder.iterdir():
            if not image_path.is_file():
                continue

            category = get_category(image_path.name)

            if category is None:
                continue

            try:
                with Image.open(image_path) as image:
                    image = image.convert("RGB")
                    image = image.resize(IMAGE_SIZE)

                    output_path = (
                        PROCESSED_DIR
                        / split
                        / category
                        / image_path.name
                    )

                    image.save(output_path)

                    if mini_counts[category] < MINI_LIMIT:
                        mini_path = (
                            MINI_DIR
                            / split
                            / category
                            / image_path.name
                        )

                        image.save(mini_path)
                        mini_counts[category] += 1

            except Exception as e:
                print(f"Error processing {image_path}: {e}")


def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {RAW_DIR}"
        )

    prepare_directories()
    process_dataset()

    print("Done!")


if __name__ == "__main__":
    main()