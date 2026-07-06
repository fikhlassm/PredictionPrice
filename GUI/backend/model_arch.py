"""
Arsitektur DNN, harus PERSIS SAMA dengan yang dipakai saat training
(lihat fungsi build_dnn di script training). Dipakai untuk membangun
ulang model lalu me-load weights saja -- pendekatan ini jauh lebih
tahan terhadap perbedaan versi TensorFlow/Keras dibanding memuat file
.keras utuh dengan keras.models.load_model().
"""

from tensorflow import keras
from tensorflow.keras import layers


def build_dnn(input_dim: int) -> keras.Model:
    model = keras.Sequential(name="DNN_Regressor")
    model.add(keras.Input(shape=(input_dim,)))

    for units, drop in [(256, 0.3), (128, 0.3), (64, 0.2), (32, 0.2)]:
        model.add(layers.Dense(units, kernel_initializer="he_normal"))
        model.add(layers.BatchNormalization())
        model.add(layers.Activation("relu"))
        model.add(layers.Dropout(drop))

    model.add(layers.Dense(1, activation="linear"))
    return model