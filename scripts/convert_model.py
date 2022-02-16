import tensorflow as tf

# Convert the model

def convert(dir):
    converter = tf.lite.TFLiteConverter.from_saved_model(dir)  # path to the SavedModel directory
    tflite_model = converter.convert()
    return tflite_model


tflite_model = convert("/home/macrodrigues/code/macrodrigues/my_projects/butterfly_detector/butterfly_detector/models/model_5022022")

# Save the model.
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)
