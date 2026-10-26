
import json
from pathlib import Path

import tensorflow as tf

# Dataset folder inside your existing project
DATA_DIR = Path(__file__).parent / "miaze"
OUTPUT_DIR = Path(__file__).parent / "models"

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 8
SEED = 42

# Verify the dataset
if not DATA_DIR.exists():
    raise FileNotFoundError(f"Dataset folder not found: {DATA_DIR}")

class_folders = sorted(
    folder.name for folder in DATA_DIR.iterdir()
    if folder.is_dir()
)

if len(class_folders) != 4:
    raise ValueError(
        f"Expected 4 class folders, found: {class_folders}"
    )

print("Classes found:", class_folders)

for folder in class_folders:
    count = sum(
        1 for p in (DATA_DIR / folder).rglob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
    )
    print(f"{folder}: {count} images")
    if count == 0:
        raise ValueError(f"No images found in {folder}")

# Load training and validation data
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

class_names = train_ds.class_names
print("Model label order:", class_names)

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# Transfer learning with MobileNetV2
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

inputs = tf.keras.Input(shape=(224, 224, 3))
x = tf.keras.layers.RandomFlip("horizontal")(inputs)
x = tf.keras.layers.RandomRotation(0.1)(x)
x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
x = base_model(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.2)(x)
outputs = tf.keras.layers.Dense(
    len(class_names), activation="softmax"
)(x)

model = tf.keras.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Save the best model based on validation loss
model_path = OUTPUT_DIR / "maize_disease_model.keras"

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        str(model_path),
        monitor="val_loss",
        save_best_only=True
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True
    )
]

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks
)

# Save class labels in the exact prediction order
with open(OUTPUT_DIR / "maize_classes.json", "w") as f:
    json.dump(class_names, f, indent=2)

print("\nTraining finished!")
print("Model:", model_path)
print("Labels:", OUTPUT_DIR / "maize_classes.json")
print("Final validation accuracy:",
      round(max(history.history["val_accuracy"]) * 100, 2), "%")
