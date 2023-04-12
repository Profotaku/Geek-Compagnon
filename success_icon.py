from matplotlib import gridspec
import matplotlib.pylab as plt
import numpy as np
import tensorflow as tf
from tensorflow_hub import load
from PIL import Image
from collections import Counter

def get_dominant_color(pil_img): #if we want adapt success-icon to getted image
    image = pil_img.resize((150, 150))  # optional, to reduce time
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    pixels = list(image.getdata())
    pixel_count = Counter(pixels)
    return pixel_count.most_common(1)[0][0]

def load_image(image_path, image_size=(320, 320)):
    img = tf.io.decode_image(tf.io.read_file(image_path),channels=3, dtype=tf.float32)[tf.newaxis, ...]
    img = tf.image.resize(img, image_size, preserve_aspect_ratio=True)
    return img



def visualize(images, titles=('',)):
    noi = len(images)
    image_sizes = [image.shape[1] for image in images]
    w = (image_sizes[0] * 6) // 320
    plt.figure(figsize=(w * noi, w))
    grid_look = gridspec.GridSpec(1, noi, width_ratios=image_sizes)

    for i in range(noi):
        plt.subplot(grid_look[i])
        plt.imshow(images[i][0], aspect='equal')
        plt.axis('off')
        plt.title(titles[i])
        plt.savefig("final.jpg")
        plt.show()

def export_image(tf_img):
    tf_img = tf_img*255
    tf_img = np.array(tf_img, dtype=np.uint8)
    if np.ndim(tf_img)>3:
        assert tf_img.shape[0] == 1
        img = tf_img[0]
    else:
        img = tf_img[0]
    return Image.fromarray(img)

def square_crop(img):
    if len(img.shape) == 3:
        height, width = img.shape.dims[0].value, img.shape.dims[1].value
    else:
        height, width = img.shape.dims[1].value, img.shape.dims[2].value
    size = min(height, width)
    y1 = (height - size) // 2
    x1 = (width - size) // 2
    crop_img = tf.image.crop_to_bounding_box(img, y1, x1, size, size)
    return crop_img
def stylize_image(id_fiche):
    base_image_path = f'static/images/fiches/{str(id_fiche)}/success.jpg'
    original_image = load_image(base_image_path)
    o = load_image(base_image_path)
    #crop original image to get a square image

    original_image = square_crop(original_image)
    style_image = load_image("tf_model_style/style.jpg")

    style_image = tf.nn.avg_pool(style_image, ksize=[3,3], strides=[1,1], padding='VALID')
    stylize_model = load('tf_model_style')

    results = stylize_model(tf.constant(original_image), tf.constant(style_image))
    stylized_photo = results[0]

    export_image(stylized_photo).save(base_image_path, optimize=True, quality=95, progressive=True)