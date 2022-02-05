# import kivy dependencies
import numpy as np
import os
from PIL import Image
from kivy.app import App
from tensorflow.keras import models
from scripts.transfer_learning import train_gen
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

PATH = os.path.dirname(os.path.dirname(__file__))

butterfly = 'class'
prediction = 'confidence'

# set window size
Window.size = (500, 550)


class cameraApp(App):

    def build(self):
        global cam
        global prediction
        global butterfly
        # create camera instance
        self.cam = Camera(index=1)

        # create button
        self.btn = Button(
            text="Capture",
            size_hint=(.1, .1),
            font_size=35,
            background_color='green',
            on_press=self.capture_image)

        # create label
        self.lbl_class = Label(
            text=butterfly,
            size_hint=(.1, .1))

        self.lbl_conf = Label(
            text=prediction,
            size_hint=(.1, .1))

        # create grid layout
        layout = GridLayout(rows=4, cols=1)

        # add widgets in layout
        layout.add_widget(self.cam)
        layout.add_widget(self.btn)
        layout.add_widget(self.lbl_class)
        layout.add_widget(self.lbl_conf)

        return layout

    def capture_image(self, *args):
        global cam
        global butterfly
        global prediction

        # save captured image
        self.cam.export_to_png(f"{PATH}\\app\\img.png")
        butterfly, prediction = self.predict()
        self.lbl_class.text = butterfly
        self.lbl_conf.text = prediction
        print(butterfly)
        print(prediction)

    def predict(self, model='model_4022022'):
        butterflies = list(train_gen.class_indices.keys())
        model_to_pred = models.load_model(f"{PATH}\models\{model}")
        img = Image.open(f"{PATH}\\app\\img.png")
        img_arr = np.array(img.resize((150, 150)))
        img_arr = img_arr[:, :, :3]
        img_arr = np.expand_dims(img_arr, axis=0)
        pred = list(model_to_pred.predict(img_arr)[0])
        preds = dict(zip(butterflies, pred))
        print(preds)
        best = max(preds, key=preds.get)

        return best, str(preds[best]*100)


if __name__ == '__main__':
    # run app
    cameraApp().run()
