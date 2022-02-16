import logging
import os
import unittest
from io import BytesIO

import pytest
from PIL import Image, TiffImagePlugin
from PIL.TiffImagePlugin import RESOLUTION_UNIT, X_RESOLUTION, Y_RESOLUTION

from .helper import PillowTestCase, hopper, is_pypy, is_win32

logger = logging.getLogger(__name__)


class TestFileTiff(PillowTestCase):
    def test_sanity(self):

        filename = self.tempfile("temp.tif")

        hopper("RGB").save(filename)

        with Image.open(filename) as im:
            im.load()
        self.assertEqual(im.mode, "RGB")
        self.assertEqual(im.size, (128, 128))
        self.assertEqual(im.format, "TIFF")

        hopper("1").save(filename)
        with Image.open(filename):
            pass

        hopper("L").save(filename)
        with Image.open(filename):
            pass

        hopper("P").save(filename)
        with Image.open(filename):
            pass

        hopper("RGB").save(filename)
        with Image.open(filename):
            pass

        hopper("I").save(filename)
        with Image.open(filename):
            pass

    @unittest.skipIf(is_pypy(), "Requires CPython")
    def test_unclosed_file(self):
        def open():
            im = Image.open("Tests/images/multipage.tiff")
            im.load()

        self.assert_warning(ResourceWarning, open)

    def test_closed_file(self):
        def open():
            im = Image.open("Tests/images/multipage.tiff")
            im.load()
            im.close()

        self.assert_warning(None, open)

    def test_context_manager(self):
        def open():
            with Image.open("Tests/images/multipage.tiff") as im:
                im.load()

        self.assert_warning(None, open)

    def test_mac_tiff(self):
        # Read RGBa images from macOS [@PIL136]

        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:
            self.assertEqual(im.mode, "RGBA")
            self.assertEqual(im.size, (55, 43))
            self.assertEqual(im.tile, [("raw", (0, 0, 55, 43), 8, ("RGBa", 0, 1))])
            im.load()

            self.assert_image_similar_tofile(im, "Tests/images/pil136.png", 1)

    def test_wrong_bits_per_sample(self):
        with Image.open("Tests/images/tiff_wrong_bits_per_sample.tiff") as im:
            self.assertEqual(im.mode, "RGBA")
            self.assertEqual(im.size, (52, 53))
            self.assertEqual(im.tile, [("raw", (0, 0, 52, 53), 160, ("RGBA", 0, 1))])
            im.load()

    def test_set_legacy_api(self):
        ifd = TiffImagePlugin.ImageFileDirectory_v2()
        with self.assertRaises(Exception) as e:
            ifd.legacy_api = None
        self.assertEqual(str(e.exception), "Not allowing setting of legacy api")

    def test_xyres_tiff(self):
        filename = "Tests/images/pil168.tif"
        with Image.open(filename) as im:

            # legacy api
            self.assertIsInstance(im.tag[X_RESOLUTION][0], tuple)
            self.assertIsInstance(im.tag[Y_RESOLUTION][0], tuple)

            # v2 api
            self.assertIsInstance(im.tag_v2[X_RESOLUTION], TiffImagePlugin.IFDRational)
            self.assertIsInstance(im.tag_v2[Y_RESOLUTION], TiffImagePlugin.IFDRational)

            self.assertEqual(im.info["dpi"], (72.0, 72.0))

    def test_xyres_fallback_tiff(self):
        filename = "Tests/images/compression.tif"
        with Image.open(filename) as im:

            # v2 api
            self.assertIsInstance(im.tag_v2[X_RESOLUTION], TiffImagePlugin.IFDRational)
            self.assertIsInstance(im.tag_v2[Y_RESOLUTION], TiffImagePlugin.IFDRational)
            self.assertRaises(KeyError, lambda: im.tag_v2[RESOLUTION_UNIT])

            # Legacy.
            self.assertEqual(im.info["resolution"], (100.0, 100.0))
            # Fallback "inch".
            self.assertEqual(im.info["dpi"], (100.0, 100.0))

    def test_int_resolution(self):
        filename = "Tests/images/pil168.tif"
        with Image.open(filename) as im:

            # Try to read a file where X,Y_RESOLUTION are ints
            im.tag_v2[X_RESOLUTION] = 71
            im.tag_v2[Y_RESOLUTION] = 71
            im._setup()
            self.assertEqual(im.info["dpi"], (71.0, 71.0))

    def test_load_dpi_rounding(self):
        for resolutionUnit, dpi in ((None, (72, 73)), (2, (72, 73)), (3, (183, 185))):
            with Image.open(
                "Tests/images/hopper_roundDown_" + str(resolutionUnit) + ".tif"
            ) as im:
                self.assertEqual(im.tag_v2.get(RESOLUTION_UNIT), resolutionUnit)
                self.assertEqual(im.info["dpi"], (dpi[0], dpi[0]))

            with Image.open(
                "Tests/images/hopper_roundUp_" + str(resolutionUnit) + ".tif"
            ) as im:
                self.assertEqual(im.tag_v2.get(RESOLUTION_UNIT), resolutionUnit)
                self.assertEqual(im.info["dpi"], (dpi[1], dpi[1]))

    def test_save_dpi_rounding(self):
        outfile = self.tempfile("temp.tif")
        with Image.open("Tests/images/hopper.tif") as im:
            for dpi in (72.2, 72.8):
                im.save(outfile, dpi=(dpi, dpi))

                with Image.open(outfile) as reloaded:
                    reloaded.load()
                    self.assertEqual((round(dpi), round(dpi)), reloaded.info["dpi"])

    def test_save_setting_missing_resolution(self):
        b = BytesIO()
        Image.open("Tests/images/10ct_32bit_128.tiff").save(
            b, format="tiff", resolution=123.45
        )
        with Image.open(b) as im:
            self.assertEqual(float(im.tag_v2[X_RESOLUTION]), 123.45)
            self.assertEqual(float(im.tag_v2[Y_RESOLUTION]), 123.45)

    def test_invalid_file(self):
        invalid_file = "Tests/images/flower.jpg"

        self.assertRaises(SyntaxError, TiffImagePlugin.TiffImageFile, invalid_file)

        TiffImagePlugin.PREFIXES.append(b"\xff\xd8\xff\xe0")
        self.assertRaises(SyntaxError, TiffImagePlugin.TiffImageFile, invalid_file)
        TiffImagePlugin.PREFIXES.pop()

    def test_bad_exif(self):
        with Image.open("Tests/images/hopper_bad_exif.jpg") as i:
            # Should not raise struct.error.
            self.assert_warning(UserWarning, i._getexif)

    def test_save_rgba(self):
        im = hopper("RGBA")
        outfile = self.tempfile("temp.tif")
        im.save(outfile)

    def test_save_unsupported_mode(self):
        im = hopper("HSV")
        outfile = self.tempfile("temp.tif")
        self.assertRaises(IOError, im.save, outfile)

    def test_little_endian(self):
        with Image.open("Tests/images/16bit.cropped.tif") as im:
            self.assertEqual(im.getpixel((0, 0)), 480)
            self.assertEqual(im.mode, "I;16")

            b = im.tobytes()
        # Bytes are in image native order (little endian)
        self.assertEqual(b[0], ord(b"\xe0"))
        self.assertEqual(b[1], ord(b"\x01"))

    def test_big_endian(self):
        with Image.open("Tests/images/16bit.MM.cropped.tif") as im:
            self.assertEqual(im.getpixel((0, 0)), 480)
            self.assertEqual(im.mode, "I;16B")

            b = im.tobytes()
        # Bytes are in image native order (big endian)
        self.assertEqual(b[0], ord(b"\x01"))
        self.assertEqual(b[1], ord(b"\xe0"))

    def test_16bit_s(self):
        with Image.open("Tests/images/16bit.s.tif") as im:
            im.load()
            self.assertEqual(im.mode, "I")
            self.assertEqual(im.getpixel((0, 0)), 32767)
            self.assertEqual(im.getpixel((0, 1)), 0)

    def test_12bit_rawmode(self):
        """ Are we generating the same interpretation
        of the image as Imagemagick is? """

        with Image.open("Tests/images/12bit.cropped.tif") as im:
            # to make the target --
            # convert 12bit.cropped.tif -depth 16 tmp.tif
            # convert tmp.tif -evaluate RightShift 4 12in16bit2.tif
            # imagemagick will auto scale so that a 12bit FFF is 16bit FFF0,
            # so we need to unshift so that the integer values are the same.

            self.assert_image_equal_tofile(im, "Tests/images/12in16bit.tif")

    def test_32bit_float(self):
        # Issue 614, specific 32-bit float format
        path = "Tests/images/10ct_32bit_128.tiff"
        with Image.open(path) as im:
            im.load()

            self.assertEqual(im.getpixel((0, 0)), -0.4526388943195343)
            self.assertEqual(im.getextrema(), (-3.140936851501465, 3.140684127807617))

    def test_unknown_pixel_mode(self):
        self.assertRaises(
            IOError, Image.open, "Tests/images/hopper_unknown_pixel_mode.tif"
        )

    def test_n_frames(self):
        for path, n_frames in [
            ["Tests/images/multipage-lastframe.tif", 1],
            ["Tests/images/multipage.tiff", 3],
        ]:
            with Image.open(path) as im:
                self.assertEqual(im.n_frames, n_frames)
                self.assertEqual(im.is_animated, n_frames != 1)

    def test_eoferror(self):
        with Image.open("Tests/images/multipage-lastframe.tif") as im:
            n_frames = im.n_frames

            # Test seeking past the last frame
            self.assertRaises(EOFError, im.seek, n_frames)
            self.assertLess(im.tell(), n_frames)

            # Test that seeking to the last frame does not raise an error
            im.seek(n_frames - 1)

    def test_multipage(self):
        # issue #862
        with Image.open("Tests/images/multipage.tiff") as im:
            # file is a multipage tiff: 10x10 green, 10x10 red, 20x20 blue

            im.seek(0)
            self.assertEqual(im.size, (10, 10))
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (0, 128, 0))

            im.seek(1)
            im.load()
            self.assertEqual(im.size, (10, 10))
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (255, 0, 0))

            im.seek(0)
            im.load()
            self.assertEqual(im.size, (10, 10))
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (0, 128, 0))

            im.seek(2)
            im.load()
            self.assertEqual(im.size, (20, 20))
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (0, 0, 255))

    def test_multipage_last_frame(self):
        with Image.open("Tests/images/multipage-lastframe.tif") as im:
            im.load()
            self.assertEqual(im.size, (20, 20))
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (0, 0, 255))

    def test___str__(self):
        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:

            # Act
            ret = str(im.ifd)

            # Assert
            self.assertIsInstance(ret, str)

    def test_dict(self):
        # Arrange
        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:

            # v2 interface
            v2_tags = {
                256: 55,
                257: 43,
                258: (8, 8, 8, 8),
                259: 1,
                262: 2,
                296: 2,
                273: (8,),
                338: (1,),
                277: 4,
                279: (9460,),
                282: 72.0,
                283: 72.0,
                284: 1,
            }
            self.assertEqual(dict(im.tag_v2), v2_tags)

            # legacy interface
            legacy_tags = {
                256: (55,),
                257: (43,),
                258: (8, 8, 8, 8),
                259: (1,),
                262: (2,),
                296: (2,),
                273: (8,),
                338: (1,),
                277: (4,),
                279: (9460,),
                282: ((720000, 10000),),
                283: ((720000, 10000),),
                284: (1,),
            }
            self.assertEqual(dict(im.tag), legacy_tags)

    def test__delitem__(self):
        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:
            len_before = len(dict(im.ifd))
            del im.ifd[256]
            len_after = len(dict(im.ifd))
            self.assertEqual(len_before, len_after + 1)

    def test_load_byte(self):
        for legacy_api in [False, True]:
            ifd = TiffImagePlugin.ImageFileDirectory_v2()
            data = b"abc"
            ret = ifd.load_byte(data, legacy_api)
            self.assertEqual(ret, b"abc")

    def test_load_string(self):
        ifd = TiffImagePlugin.ImageFileDirectory_v2()
        data = b"abc\0"
        ret = ifd.load_string(data, False)
        self.assertEqual(ret, "abc")

    def test_load_float(self):
        ifd = TiffImagePlugin.ImageFileDirectory_v2()
        data = b"abcdabcd"
        ret = ifd.load_float(data, False)
        self.assertEqual(ret, (1.6777999408082104e22, 1.6777999408082104e22))

    def test_load_double(self):
        ifd = TiffImagePlugin.ImageFileDirectory_v2()
        data = b"abcdefghabcdefgh"
        ret = ifd.load_double(data, False)
        self.assertEqual(ret, (8.540883223036124e194, 8.540883223036124e194))

    def test_seek(self):
        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:
            im.seek(0)
            self.assertEqual(im.tell(), 0)

    def test_seek_eof(self):
        filename = "Tests/images/pil136.tiff"
        with Image.open(filename) as im:
            self.assertEqual(im.tell(), 0)
            self.assertRaises(EOFError, im.seek, -1)
            self.assertRaises(EOFError, im.seek, 1)

    def test__limit_rational_int(self):
        from PIL.TiffImagePlugin import _limit_rational

        value = 34
        ret = _limit_rational(value, 65536)
        self.assertEqual(ret, (34, 1))

    def test__limit_rational_float(self):
        from PIL.TiffImagePlugin import _limit_rational

        value = 22.3
        ret = _limit_rational(value, 65536)
        self.assertEqual(ret, (223, 10))

    def test_4bit(self):
        test_file = "Tests/images/hopper_gray_4bpp.tif"
        original = hopper("L")
        with Image.open(test_file) as im:
            self.assertEqual(im.size, (128, 128))
            self.assertEqual(im.mode, "L")
            self.assert_image_similar(im, original, 7.3)

    def test_gray_semibyte_per_pixel(self):
        test_files = (
            (
                24.8,  # epsilon
                (  # group
                    "Tests/images/tiff_gray_2_4_bpp/hopper2.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper2I.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper2R.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper2IR.tif",
                ),
            ),
            (
                7.3,  # epsilon
                (  # group
                    "Tests/images/tiff_gray_2_4_bpp/hopper4.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper4I.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper4R.tif",
                    "Tests/images/tiff_gray_2_4_bpp/hopper4IR.tif",
                ),
            ),
        )
        original = hopper("L")
        for epsilon, group in test_files:
            with Image.open(group[0]) as im:
                self.assertEqual(im.size, (128, 128))
                self.assertEqual(im.mode, "L")
                self.assert_image_similar(im, original, epsilon)
                for file in group[1:]:
                    with Image.open(file) as im2:
                        self.assertEqual(im2.size, (128, 128))
                        self.assertEqual(im2.mode, "L")
                        self.assert_image_equal(im, im2)

    def test_with_underscores(self):
        kwargs = {"resolution_unit": "inch", "x_resolution": 72, "y_resolution": 36}
        filename = self.tempfile("temp.tif")
        hopper("RGB").save(filename, **kwargs)
        with Image.open(filename) as im:

            # legacy interface
            self.assertEqual(im.tag[X_RESOLUTION][0][0], 72)
            self.assertEqual(im.tag[Y_RESOLUTION][0][0], 36)

            # v2 interface
            self.assertEqual(im.tag_v2[X_RESOLUTION], 72)
            self.assertEqual(im.tag_v2[Y_RESOLUTION], 36)

    def test_roundtrip_tiff_uint16(self):
        # Test an image of all '0' values
        pixel_value = 0x1234
        infile = "Tests/images/uint16_1_4660.tif"
        with Image.open(infile) as im:
            self.assertEqual(im.getpixel((0, 0)), pixel_value)

            tmpfile = self.tempfile("temp.tif")
            im.save(tmpfile)

            with Image.open(tmpfile) as reloaded:
                self.assert_image_equal(im, reloaded)

    def test_strip_raw(self):
        infile = "Tests/images/tiff_strip_raw.tif"
        with Image.open(infile) as im:
            self.assert_image_equal_tofile(im, "Tests/images/tiff_adobe_deflate.png")

    def test_strip_planar_raw(self):
        # gdal_translate -of GTiff -co INTERLEAVE=BAND \
        # tiff_strip_raw.tif tiff_strip_planar_raw.tiff
        infile = "Tests/images/tiff_strip_planar_raw.tif"
        with Image.open(infile) as im:
            self.assert_image_equal_tofile(im, "Tests/images/tiff_adobe_deflate.png")

    def test_strip_planar_raw_with_overviews(self):
        # gdaladdo tiff_strip_planar_raw2.tif 2 4 8 16
        infile = "Tests/images/tiff_strip_planar_raw_with_overviews.tif"
        with Image.open(infile) as im:
            self.assert_image_equal_tofile(im, "Tests/images/tiff_adobe_deflate.png")

    def test_tiled_planar_raw(self):
        # gdal_translate -of GTiff -co TILED=YES -co BLOCKXSIZE=32 \
        # -co BLOCKYSIZE=32 -co INTERLEAVE=BAND \
        # tiff_tiled_raw.tif tiff_tiled_planar_raw.tiff
        infile = "Tests/images/tiff_tiled_planar_raw.tif"
        with Image.open(infile) as im:
            self.assert_image_equal_tofile(im, "Tests/images/tiff_adobe_deflate.png")

    def test_palette(self):
        for mode in ["P", "PA"]:
            outfile = self.tempfile("temp.tif")

            im = hopper(mode)
            im.save(outfile)

            with Image.open(outfile) as reloaded:
                self.assert_image_equal(im.convert("RGB"), reloaded.convert("RGB"))

    def test_tiff_save_all(self):
        mp = BytesIO()
        with Image.open("Tests/images/multipage.tiff") as im:
            im.save(mp, format="tiff", save_all=True)

        mp.seek(0, os.SEEK_SET)
        with Image.open(mp) as im:
            self.assertEqual(im.n_frames, 3)

        # Test appending images
        mp = BytesIO()
        im = Image.new("RGB", (100, 100), "#f00")
        ims = [Image.new("RGB", (100, 100), color) for color in ["#0f0", "#00f"]]
        im.copy().save(mp, format="TIFF", save_all=True, append_images=ims)

        mp.seek(0, os.SEEK_SET)
        with Image.open(mp) as reread:
            self.assertEqual(reread.n_frames, 3)

        # Test appending using a generator
        def imGenerator(ims):
            yield from ims

        mp = BytesIO()
        im.save(mp, format="TIFF", save_all=True, append_images=imGenerator(ims))

        mp.seek(0, os.SEEK_SET)
        with Image.open(mp) as reread:
            self.assertEqual(reread.n_frames, 3)

    def test_saving_icc_profile(self):
        # Tests saving TIFF with icc_profile set.
        # At the time of writing this will only work for non-compressed tiffs
        # as libtiff does not support embedded ICC profiles,
        # ImageFile._save(..) however does.
        im = Image.new("RGB", (1, 1))
        im.info["icc_profile"] = "Dummy value"

        # Try save-load round trip to make sure both handle icc_profile.
        tmpfile = self.tempfile("temp.tif")
        im.save(tmpfile, "TIFF", compression="raw")
        with Image.open(tmpfile) as reloaded:
            self.assertEqual(b"Dummy value", reloaded.info["icc_profile"])

    def test_close_on_load_exclusive(self):
        # similar to test_fd_leak, but runs on unixlike os
        tmpfile = self.tempfile("temp.tif")

        with Image.open("Tests/images/uint16_1_4660.tif") as im:
            im.save(tmpfile)

        im = Image.open(tmpfile)
        fp = im.fp
        self.assertFalse(fp.closed)
        im.load()
        self.assertTrue(fp.closed)

    def test_close_on_load_nonexclusive(self):
        tmpfile = self.tempfile("temp.tif")

        with Image.open("Tests/images/uint16_1_4660.tif") as im:
            im.save(tmpfile)

        with open(tmpfile, "rb") as f:
            im = Image.open(f)
            fp = im.fp
            self.assertFalse(fp.closed)
            im.load()
            self.assertFalse(fp.closed)

    # Ignore this UserWarning which triggers for four tags:
    # "Possibly corrupt EXIF data.  Expecting to read 50404352 bytes but..."
    @pytest.mark.filterwarnings("ignore:Possibly corrupt EXIF data")
    def test_string_dimension(self):
        # Assert that an error is raised if one of the dimensions is a string
        with self.assertRaises(ValueError):
            Image.open("Tests/images/string_dimension.tiff")


@unittest.skipUnless(is_win32(), "Windows only")
class TestFileTiffW32(PillowTestCase):
    def test_fd_leak(self):
        tmpfile = self.tempfile("temp.tif")

        # this is an mmaped file.
        with Image.open("Tests/images/uint16_1_4660.tif") as im:
            im.save(tmpfile)

        im = Image.open(tmpfile)
        fp = im.fp
        self.assertFalse(fp.closed)
        self.assertRaises(WindowsError, os.remove, tmpfile)
        im.load()
        self.assertTrue(fp.closed)

        # this closes the mmap
        im.close()

        # this should not fail, as load should have closed the file pointer,
        # and close should have closed the mmap
        os.remove(tmpfile)
