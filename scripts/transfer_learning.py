from tensorflow.keras import layers, models
from keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras import optimizers
from tensorflow.keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np
import os

PATH = os.path.dirname(os.path.dirname(__file__))
PATH_TEST = f"{PATH}/raw_data/test"

imgs_gen =  ImageDataGenerator(rotation_range=20,
                             width_shift_range=0.3,
                             height_shift_range=0.3,
                             rescale=1/255,
                             shear_range=0.3,
                             zoom_range=0.3,
                             horizontal_flip=True,
                             validation_split=0.23,
                             fill_mode='nearest')

train_gen = imgs_gen.flow_from_directory(f"{PATH}/raw_data/train",
                                            class_mode = 'categorical',
                                            target_size=(150, 150),
                                            subset='training',
                                            batch_size=16)

val_gen = imgs_gen.flow_from_directory(f"{PATH}/raw_data/train",
                                            target_size=(150, 150),
                                            batch_size = 16,
                                            subset='validation',
                                            class_mode = 'categorical')

def compile_model():
    """Uses VGG16 for transfer learning and applies additional layers.
    Then it compiles the model for a multiclass classification problem."""
    base_model = VGG16(weights="imagenet",
                    include_top=False,
                    input_shape=(150, 150, 3))
    flattening_layer = layers.Flatten()
    dense_layer_1 = layers.Dense(126, activation='relu')
    dense_layer_2 = layers.Dense(50, activation='relu')
    dense_layer_3 = layers.Dense(32, activation='relu')
    prediction_layer = layers.Dense(12, activation = 'softmax')

    model = models.Sequential([
        base_model,
        flattening_layer,
        dense_layer_1,
        dense_layer_2,
        dense_layer_3,
        prediction_layer
    ])

    opt = optimizers.Adam(learning_rate=1e-4)
    model.compile(loss='categorical_crossentropy', # Classification with more classes
                    optimizer=opt,
                    metrics=['accuracy'])

    return model

def train_model(model,
                name_to_save = 'model_test',
                patience = 20,
                epochs = 50,
                batch_size = 32,
                steps_per_epoch = 100,
                validation_steps = 16):

    """Trains the model and saves it. Returns the history of the epochs."""
    es = EarlyStopping(monitor='val_accuracy',
                   mode='max',
                   patience=patience,
                   verbose=1,
                   restore_best_weights=True)

    history = model.fit(train_gen,
          epochs=epochs,
          verbose='auto',
          batch_size = batch_size,
          validation_data=val_gen,
          steps_per_epoch= steps_per_epoch,
          validation_steps=validation_steps,
          callbacks=[es])

    model.save(f"{PATH}/butterfly_detector/models/{name_to_save}")

    return history

def plot_history(history, axs=None, exp_name=""):
    if axs is not None:
        ax1, ax2 = axs
    else:
        f, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    if len(exp_name) > 0 and exp_name[0] != '_':
        exp_name = '_' + exp_name
    ax1.plot(history.history['loss'], label='train' + exp_name)
    ax1.plot(history.history['val_loss'], label='val' + exp_name)
    ax1.set_title('loss')
    ax1.legend()

    ax2.plot(history.history['accuracy'], label='train accuracy' + exp_name)
    ax2.plot(history.history['val_accuracy'], label='val accuracy' + exp_name)
    ax2.set_title('Accuracy')
    ax2.legend()

    return (ax1, ax2)

def check_accuracy(pick_model='model_test'):
    """" Check accuracy for each one of the test elements.
    And ouputs the final yield"""
    list_test_elements = os.listdir(PATH_TEST)
    butterflies = list(train_gen.class_indices.keys())
    model = models.load_model(f"{PATH}/butterfly_detector/models/{pick_model}")
    count = 0
    for i in list_test_elements:
        img_file = f"{PATH_TEST}/{i}"
        img = image.load_img(img_file, target_size=(150, 150))
        img_arr = image.img_to_array(img)
        img_arr = np.expand_dims(img_arr, axis=0)
        pred = list(model.predict(img_arr)[0])
        preds = dict(zip(butterflies, pred))
        new_preds = preds.copy()
        new_vals = []
        new_keys = []
        for key, value in preds.items():
            if value != 0.0:
                new_vals.append(value)
                new_keys.append(key)
        new_preds = dict(zip(new_keys, new_vals))
        print(preds)
        print('TITLE:', i.split('_')[0])
        print('PREDICTIONS:', new_preds)
        print('BEST PREDICTION:', max(preds, key=preds.get))
        if max(preds, key=preds.get) == i.split('_')[0]:
            count += 1
            print('RESULT', 'Good prediction!')
            print('\n')
        else:
            print('RESULT', 'Wrong Prediction!')
            print('\n')

    print(f"This model is {round((count)*100/len(list_test_elements), 2)}% efective.")
