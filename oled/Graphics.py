__author__ = "Stefan Mavrodiev"
__copyright__ = "Copyright 2015, Olimex LTD"
__credits__ = ["Stefan Mavrodiev"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = __author__
__email__ = "support@olimex.com"

from .OLED import OLED


class Graphics(OLED):

    def __init__(self):
        """
        Default constructor

        """
        pass

    @classmethod
    def draw_pixel(cls, x, y, on=True):
        """
        Draw single pixel to video buffer

        :param x: X location
        :param y: Y location
        :param on:  True - Set pixel, False - clear pixel
        """
        if x in range(128) and y in range(64):
            if on:
                OLED.video_buffer[(y//8)*128 + x] |= (1 << (y % 8))
            else:
                OLED.video_buffer[(y//8)*128 + x] &= ~(1 << (y % 8))

    @classmethod
    def draw_line(cls, x0, y0, x1, y1):
        """
        Draw single line

        :param x0: Start x location
        :param y0: Start y location
        :param x1: End x location
        :param y1: End y location
        """

        # Using Bresenham's line algorithm
        dx = x1 - x0
        dy = y1 - y0
        D = 2*dy - dx
        cls.draw_pixel(x0, y0)
        y = y0

        for x in range(x0+1, x1+1):
            if D > 0:
                y += 1
                cls.draw_pixel(x, y)
                D += (2*dy - 2*dx)
            else:
                cls.draw_pixel(x, y)
                D += 2*dy

    @classmethod
    def draw_circle(cls, x0, y0, r):
        """
        Draw singled circle

        :param x0: Center x location
        :param y0: Center y location
        :param r: Radius
        """
        x = r
        y = 0
        decision_over_2 = 1 - x

        while x >= y:
            cls.draw_pixel(x + x0, y + y0)
            cls.draw_pixel(y + x0, x + y0)
            cls.draw_pixel(-x + x0, y + y0)
            cls.draw_pixel(-y + x0, x + y0)
            cls.draw_pixel(-x + x0, -y + y0)
            cls.draw_pixel(-y + x0, -x + y0)
            cls.draw_pixel(x + x0, -y + y0)
            cls.draw_pixel(y + x0, -x + y0)
            y += 1

            if decision_over_2 <= 0:
                decision_over_2 += 2 * y + 1
            else:
                x -= 1
                decision_over_2 += 2 * (y - x) + 1