from config import MODEL_PATH
from keras import layers
from os.path import isfile
import keras
import numpy as np


class Model:

    def __init__(self):
        self.model = keras.Sequential()
        self.model.add(layers.Dense(128, activation="leaky_relu"))
        self.model.add(layers.Dense(32, activation="leaky_relu"))
        self.model.add(layers.Dense(1))
        self.model.compile(
            optimizer=keras.optimizers.RMSprop(),
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )

        if isfile(MODEL_PATH):
            self.model.load_weights(MODEL_PATH)

    def save(self):
        self.model.save_weights(MODEL_PATH)

    def train(self, X, y):
        self.model.fit(X, y, batch_size=64, epochs=50, validation_data=(X, y))

    def predict(self, X):
        y = self.model.predict(X, batch_size=64)

        return np.reshape(y, (y.shape[0], ))
