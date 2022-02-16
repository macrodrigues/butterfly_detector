import numpy as np
import os
PATH = os.path.dirname(os.path.dirname(__file__))
from kivy.app import App
from PIL import Image
from transfer_learning import train_gen
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from model import TensorFlowModel
from kivy.core.window import Window

# set window size
Window.size = (200, 200)

butterfly = 'class'
prediction = 'confidence'

class cameraApp(App):

    def build(self):
        # create camera instance
        self.cam = Camera(index=0)

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

        # save captured image
        self.cam.export_to_png(f"{PATH}/app/img.png")
        butterfly, prediction = self.predict()
        self.lbl_class.text = butterfly
        self.lbl_conf.text = prediction

    def predict(self, model='model.tflite'):
        butterflies = list(train_gen.class_indices.keys())

        # Load TFLite model
        model_to_pred = TensorFlowModel()
        model_to_pred.load(f"{PATH}/models/{model}")

        # Read image and predict
        img = Image.open(f"{PATH}/app/img.png")
        img_arr = np.array(img.resize((150, 150)), np.float32)
        img_arr = img_arr[:, :, :3]
        img_arr = np.expand_dims(img_arr, axis=0)
        preds = dict(zip(butterflies, list(model_to_pred.pred(img_arr)[0])))
        best = max(preds, key=preds.get)

        return best, str(preds[best]*100)

if __name__ == '__main__':
    # run app
    cameraApp().run()
