from PIL import Image

from .helper import PillowTestCase


class TestFilePcd(PillowTestCase):
    def test_load_raw(self):
        with Image.open("Tests/images/hopper.pcd") as im:
            im.load()  # should not segfault.

        # Note that this image was created with a resized hopper
        # image, which was then converted to pcd with imagemagick
        # and the colors are wonky in Pillow.  It's unclear if this
        # is a pillow or a convert issue, as other images not generated
        # from convert look find on pillow and not imagemagick.

        # target = hopper().resize((768,512))
        # self.assert_image_similar(im, target, 10)
