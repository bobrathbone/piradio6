# -*- coding: utf-8 -*-

__author__ = "Stefan Mavrodiev"
__copyright__ = "Copyright 2015, Olimex LTD"
__credits__ = ["Stefan Mavrodiev"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = __author__
__email__ = "support@olimex.com"


import smbus
import sys


class MethodError(Exception):
    pass


class OLED:

    oled_height = 64
    oled_width = 128
    video_buffer = [0]*(oled_height * oled_width // 8)

    # Define some global values
    RIGHT_SCROLL = 0
    LEFT_SCROLL = 1

    def __init__(self, i2c, address=0x3c):
        # Communication parameters
        self.bus = None
        self.__i2c_device = i2c
        self.__i2c_address = address

        # Communication constants
        self.__next_is_command = 0x80
        self.__next_is_data = 0x40

        # Oled default parameters
        self.__oled_contrast = 0x7f
        self.__oled_entire_display_on = False
        self.__oled_inverse_display = False

        self.__oled_vertical_offset = None

        self.__oled_lower_column_start = 0
        self.__oled_higher_column_start = 0
        self.__oled_mode = 0x2
        self.__oled_column_start_address = 0
        self.__oled_column_end_address = 127
        self.__oled_page_start_address = 0
        self.__oled_page_end_address = 0

        self.__oled_start_line = 0
        self.__oled_segment_remap = False
        self.__oled_mux_ratio = 64
        self.__oled_remapped = False
        self.__oled_display_offset = 0
        self.__oled_pin_configuration = True
        self.__oled_com_remap = False

        self.__oled_clock_divide = 0
        self.__oled_osc_freq = 0x08
        self.__oled_phase1 = 0x02
        self.__oled_phase2 = 0x02
        self.__oled_deselect_level = 0x01

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def begin(self):
        """
        Create communication object

        """
        self.bus = smbus.SMBus(self.i2c)

    def close(self):
        """
        Close I2C bus and delete communication object

        """
        self.bus.close()
        del self.bus

    def initialize(self):
        """
        Basic display initialization

        """

        # Turn off display
        self.set_display_on_off(on=False)

        # Set MUX ratio
        self.set_multiplex_ratio(ratio=63)

        # Set Display Offset
        self.set_display_offset(offset=0)

        # Set Display Start Line
        self.set_display_start_line(start_line=0)

        # Set Segment re-map
        self.set_segment_remap(remap=True)

        # Set COM Pins hardware configuration
        self.set_com_pins_configuration(configuration=True, remap=False)

        # Set contrast Control
        self.set_contrast_control(contrast=0x7f)

        # Disable Entire Display On
        self.entire_display_on(status=False)

        # Set Normal Display
        self.set_inverse_display(inverse=False)

        # Set Osc Frequency
        self.set_display_clock(divider=0, osc_freq=15)

        # Enabled charge pump regulator
        self.charge_pump_setting(on=True)

        # Display On
        self.set_display_on_off(on=True)

    def send_data(self, data):
        """
        Send data in packets by 16 bytes

        :param data: Data to be send
        """
        data_len = len(data)//16

        for i in range(data_len):
            temp = data[16*i:16*(i+1)]
            if temp:
                self.__send_data(temp)

    def __send_data(self, data):
        """
        Send one packet via i2c bus

        :param data: Data to be send
        """
        self.bus.write_i2c_block_data(self.__i2c_address, self.__next_is_data, data)

    def __send_command(self, command):
        """
        Send command to SSD1306 controller
        :param command:
        """
        data = []
        for i in command:
            data.append(self.__next_is_command)
            data.append(i)
        self.bus.write_i2c_block_data(self.__i2c_address, data[0], data[1:])

    def clear(self, update=True):
        """
        Clear video buffer

        :param update: If true send the empty buffer to the controller
        """
        for i in range(len(self.video_buffer)):
            self.video_buffer[i] = 0x00

        # Send the empty buffer
        if update:
            self.update()

    def update(self):
        """
        Send video buffer to the controller

        """
        self.send_data(self.video_buffer)


    @staticmethod
    def check_int(data, lower_range, upper_range):
        if lower_range >= upper_range:
            raise ValueError("Lower range cannot be greater that the upper")
        if not isinstance(data, int):
            raise TypeError("Value must be integer")
        if data > upper_range or data < lower_range:
            raise ValueError("Invalid value")

    @property
    def i2c(self):
        return self.__i2c_device

    @i2c.setter
    def i2c(self, i2c):
        self.__i2c_device = i2c

    @property
    def address(self):
        return self.__i2c_address

    @address.setter
    def address(self, address):
        # Check if address is valid
        self.check_int(address, 0x3c, 0x3d)
        self.__i2c_address = address

    @property
    def height(self):
        return self.oled_height

    @property
    def width(self):
        return self.oled_width

    @property
    def contrast(self):
        return self.__oled_contrast

    @contrast.setter
    def contrast(self, contrast):
        self.check_int(contrast, 0, 0xff)
        self.__oled_contrast = contrast

    @property
    def mode(self):
        return self.__oled_mode

    # 1. Fundamental Command Table
    def set_contrast_control(self, contrast):
        """
        Set Contrast Control for BANK0 (81h)

        This command sets the Contrast Setting of the display. The chip has 256 contrast steps from 00h to FFh. The
        segment output current increases as the contrast step value increases.

        :param contrast:    Double byte command to select 1 out of 256 contrast steps. Contrast increases as the value
                            increases. (RESET = 7Fh )
        """
        self.contrast = contrast
        self.__send_command([0x81, self.contrast])

    def entire_display_on(self, status):
        """
        Entire Display ON (A4h/A5h)

        A4h command enable display outputs according to the GDDRAM contents.If A5h command is issued, then by using A4h
        command, the display will resume to the GDDRAM contents. In other words, A4h command resumes the display from
        entire display “ON” stage. A5h command forces the entire display to be “ON”, regardless of the contents of the
        display data RAM.

        :param status:  True - Entire display ON. Output ignores RAM content
                        False - Resume to RAM content display (RESET). Output follows RAM content
        """
        self.check_int(status, 0, 1)
        self.__send_command([0xa4 | status])

    def set_inverse_display(self, inverse):
        """
        Set Normal/Inverse Display (A6h/A7h)

        This command sets the display to be either normal or inverse. In normal display a RAM data of 1 indicates an
        “ON” pixel while in inverse display a RAM data of 0 indicates an “ON” pixel.

        :param inverse: True - Inverse display
                        False - ormal display (RESET)
        """
        self.check_int(inverse, 0, 1)
        self.__send_command([0xa6 | inverse])

    def set_display_on_off(self, on):
        """
        Set Display ON/OFF (AEh/AFh)

        These single byte commands are used to turn the OLED panel display ON or OFF. When the display is ON, the
        selected circuits by Set Master Configuration command will be turned ON. When the display is OFF, those circuits
        will be turned OFF and the segment and common output are in VSS state and high impedance state, respectively.

        :param on:  True - Display ON
                    False - Display OFF
        """
        self.check_int(on, 0, 1)
        self.__send_command([0xae | on])

    # 2. Scrolling Command Table
    def deactivate_scroll(self):
        """
        Deactivate scroll (2Eh)

        This command stops the motion of scrolling. After sending 2Eh command to deactivate the scrolling action,the ram
        data needs to be rewritten.
        """
        self.__send_command([0x2e])
        self.update()

    def activate_scroll(self):
        """
        Activate Scroll (2Fh)

        This command starts the motion of scrolling and should only be issued after the scroll setup parameters have
        been defined by the scrolling setup commands :26h/27h/29h/2Ah . The setting in the last scrolling setup command
        overwrites the setting in the previous scrolling setup commands.

        The following actions are prohibited after the scrolling is activated
            1.  RAM access (Data write or read)
            2.  Changing the horizontal scroll setup parameters
        """
        self.__send_command([0x2f])

    def horizontal_scroll_setup(self, direction, start_page, end_page, speed):
        """
        Horizontal Scroll Setup (26h/27h)

        This command consists of consecutive bytes to set up the horizontal scroll parameters and determines the
        scrolling start page, end page and scrolling speed. Before issuing this command the horizontal scroll must be
        deactivated (2Eh). Otherwise, RAM content may be corrupted.

        :param direction:   0 - Right Horizontal Scroll
                            1 - Left Horizontal Scroll
        :param start_page:  Define start page address - PAGE0 ~ PAGE7
        :param end_page:    Define end page address - PAGE0 ~ PAGE7
        :param speed:       Set time interval between each roll step in terms of frame frequency:
                                0 - 5 frames
                                1 - 64 frames
                                2 - 128 frames
                                3 - 256 frames
                                4 - 3 frames
                                5 - 4 frames
                                6 - 25 frames
                                7 - 2 frames
        :raise ValueError: Start page cannot be larger than end page
        """
        self.deactivate_scroll()

        # Check for correct values
        self.check_int(direction, 0, 1)
        self.check_int(start_page, 0, 7)
        self.check_int(end_page, 0, 7)
        self.check_int(speed, 0, 7)

        # Check if start_page is bigger than end_page
        if start_page > end_page:
            raise ValueError("Start page address cannot be bigger than end page address")

        self.__send_command([0x26 | direction, 0, start_page, speed, end_page, 0x00, 0xFF])

    def vertical_and_horizontal_scroll_setup(self, direction, start_page, end_page, speed, vertical_offset):
        """
         Continuous Vertical and Horizontal Scroll Setup (29h/2Ah)

        This command consists of 6 consecutive bytes to set up the continuous vertical scroll parameters and determines
        the scrolling start page, end page, scrolling speed and vertical scrolling offset.

        The bytes B[2:0], C[2:0] and D[2:0] of command 29h/2Ah are for the setting of the continuous horizontal
        scrolling. The byte E[5:0] is for the setting of the continuous vertical scrolling offset. All these bytes
        together are for the setting of continuous diagonal (horizontal + vertical) scrolling. If the vertical
        scrolling offset byte E[5:0] is set to zero, then only horizontal scrolling is performed (like command 26/27h).

        Before issuing this command the scroll must be deactivated (2Eh). Otherwise, RAM content may be corrupted.

        :param direction:       0 - Vertical and Right Horizontal Scroll
                                1 - Vertical and Left Horizontal Scroll
        :param start_page:      Define start page address - PAGE0 ~ PAGE7
        :param end_page:        Define end page address -   PAGE0 ~ PAGE7
        :param speed:           Set time interval between each roll step in terms of frame frequency:
                                0 - 5 frames
                                1 - 64 frames
                                2 - 128 frames
                                3 - 256 frames
                                4 - 3 frames
                                5 - 4 frames
                                6 - 25 frames
                                7 - 2 frames
        :param vertical_offset: Vertical scrolling offset e.g.
                                    01h refer to offset = 1 row
                                    3Fh refer to offset = 63 rows
        :raise ValueError:      Start page cannot be larger than end page
        """
        self.deactivate_scroll()

        # Check for correct values
        self.check_int(direction, 0, 1)
        self.check_int(start_page, 0, 7)
        self.check_int(end_page, 0, 7)
        self.check_int(speed, 0, 7)
        self.check_int(vertical_offset, 0, 63)

        self.__oled_vertical_offset = vertical_offset

        # Check if start_page is bigger than end_page
        if start_page > end_page:
            raise ValueError("Start page address cannot be bigger than end page address")

        self.__send_command([0x28 | (direction + 1), 0, start_page, speed, end_page, vertical_offset])

    def set_vertical_scroll_area(self, start, count):

        """
        Set Vertical Scroll Area(A3h)

        This command consists of 3 consecutive bytes to set up the vertical scroll area. For the continuous vertical
        scroll function (command 29/2Ah), the number of rows that in vertical scrolling can be set smaller or equal to
        the MUX ratio.

        :param start:       Set No. of rows in top fixed area. The No. of rows in top fixed area is referenced to the
                            top of the GDDRAM (i.e. row 0).[RESET =0]

        :param count:       Set No. of rows in scroll area. This is the number of rows to be used for vertical
                            scrolling. The scroll area starts in the first row below the top fixed area. [RESET = 64]

        :raise ValueError:
        """
        self.check_int(start, 0, 63)
        self.check_int(count, 0, 63)

        if start + count > self.__oled_mux_ratio:
            raise ValueError("Start + Count cannot be larger than MUX ratio")

        if count > self.__oled_mux_ratio:
            raise ValueError("Count cannot be larger than MUX ratio")

        if not self.__oled_vertical_offset:
            raise ValueError("Vertical and horizontal scroll must be setup first")

        if not (self.__oled_vertical_offset < count):
            raise ValueError("Count cannot be smaller than vertical offset")

        if not (self.__oled_start_line < count):
            raise ValueError("Display start line must be smaller than Count")

        self.__send_command([0xa3, start, count])

    # 3. Addressing Setting Command Table
    def set_lower_column(self, column):
        """
        Set Lower Column Start Address for Page Addressing Mode (00h~0Fh)

        This command specifies the lower nibble of the 8-bit column start address for the display data RAM under Page
        Addressing Mode. The column address will be incremented by each data access.

        :param column:  Set the lower nibble of the column start address register for Page Addressing Mode using X[3:0]
                        as data bits. The initial display line register is reset to 0000b after RESET.
        :raise MethodError: This command is only for page addressing mode
        """
        if self.mode != 0x02:
            raise MethodError("\"%s\" method is only for page addressing mode" % sys._getframe().f_code.co_name)
        self.check_int(column, 0, 0xf)
        self.__send_command([0x00 | column])

    def set_higher_column(self, column):
        """
        Set Higher Column Start Address for Page Addressing Mode (10h~1Fh)

        This command specifies the higher nibble of the 8-bit column start address for the display data RAM under
        Page Addressing Mode. The column address will be incremented by each data access.

        :param column:  Set the higher nibble of the column start address register for Page Addressing Mode using X[3:0]
                        as data bits. The initial display line register is reset to 0000b after RESET.
        :raise MethodError: This command is only for page addressing mode
        """
        if self.mode != 0x02:
            raise MethodError("\"%s\" method is only for page addressing mode" % sys._getframe().f_code.co_name)
        self.check_int(column, 0, 0xf)
        self.__send_command([0x10 | column])

    def set_memory_addressing_mode(self, mode):
        """
        Set Memory Addressing Mode (20h)

        There are 3 different memory addressing mode in SSD1306: page addressing mode, horizontal addressing mode and
        vertical addressing mode. This command sets the way of memory addressing into one of the above three modes. In
        there, “COL” means the graphic display data RAM column.

        :param mode:    2 - Page addressing mode
                        In page addressing mode, after the display RAM is read/written, the column address pointer is
                        increased automatically by 1.  If the column address pointer reaches column end address, the
                        column address pointer is reset to column start address and page address pointer is not changed.
                        Users have to set the new page and column addresses in order to access the next page RAM
                        content.

                        0 - Horizontal addressing mode
                        In horizontal addressing mode, after the display RAM is read/written, the column address pointer
                        is increased automatically by 1.  If the column address pointer reaches column end address, the
                        column address pointer is reset to column start address and page address pointer is increased by
                        1. When both column and page address pointers reach the end address, the pointers are reset to
                        column start address and page start address.

                        1 - Vertical addressing mode
                        In vertical addressing mode, after the display RAM is read/written, the page address pointer is
                        increased automatically by 1.  If the page address pointer reaches the page end address, the
                        page address pointer is reset to page start address and column address pointer is increased
                        by 1. When both column and page address pointers reach the end address, the pointers are reset
                        to column start address and page start address
        """
        self.check_int(mode, 0, 2)
        self.__oled_mode = mode
        self.__send_command([0x20, 0x00 | mode])

    def set_column_address(self, column_start_address, column_end_address):
        """
        Set Column Address (21h)

        This triple byte command specifies column start address and end address of the display data RAM. This command
        also sets the column address pointer to column start address.  This pointer is used to define the current
        read/write column address in graphic display data RAM.  If horizontal address increment mode is enabled by
        command 20h, after finishing read/write one column data, it is incremented automatically to the next column
        address.  Whenever the column address pointer finishes accessing the end column address, it is reset back to
        start column address and the row address is incremented to the next row.

        :param column_start_address:    Column start address, range : 0-127d, (RESET=0d)
        :param column_end_address:      Column end address, range : 0-127d, (RESET =127d)
        :raise MethodError:  This command is only for horizontal or vertical addressing mode.
        """
        if self.mode == 0x02:
            raise MethodError("\"%s\" method cannot be used with page addressing mode" % sys._getframe().f_code.co_name)
        self.check_int(column_start_address, 0, 127)
        self.check_int(column_end_address, 0, 127)
        self.__send_command([0x21, column_start_address, column_end_address])

    def set_page_address(self, page_start_address, page_end_address):
        """
        Set Page Address (22h)

        This triple byte command specifies page start address and end address of the display data RAM. This command also
        sets the page address pointer to page start address. This pointer is used to define the current read/write page
        address in graphic display data RAM. If vertical address increment mode is enabled by command 20h, after
        finishing read/write one page data, it is incremented automatically to the next page address.  Whenever the page
        address pointer finishes accessing the end page address, it is reset back to start page address.

        :param page_start_address:  Page start Address, range : 0-7d, (RESET = 0d)
        :param page_end_address:    Page end Address, range : 0-7d, (RESET = 7d)
        :raise MethodError:  This command is only for horizontal or vertical addressing mode.
        """
        if self.mode == 0x02:
            raise MethodError("\"%s\" method cannot be used with page addressing mode" % sys._getframe().f_code.co_name)
        self.check_int(page_start_address, 0, 7)
        self.check_int(page_end_address, 0, 7)
        self.__send_command([0x22, page_start_address, page_end_address])

    def set_page_start_address(self, page):
        """
        Set Page Start Address for Page Addressing Mode (B0h~B7h)

        This command positions the page start address from 0 to 7 in GDDRAM under Page Addressing Mode.

        :param page:    Set GDDRAM Page Start Address (PAGE0~PAGE7) for Page Addressing Mode using X[2:0].
        :raise MethodError: This command is only for page addressing mode
        """
        if self.mode != 0x02:
            raise MethodError("\"%s\" method is only for page addressing mode" % sys._getframe().f_code.co_name)
        self.check_int(page, 0, 7)
        self.__send_command([0xb0 | page])

    # 4. Hardware Configuration (Panel resolution & layout related) Command Table
    def set_display_start_line(self, start_line):
        """
        Set Display Start Line (40h~7Fh)

        This command sets the Display Start Line register to determine starting address of display RAM, by selecting a
        value from 0 to 63. With value equal to 0, RAM row 0 is mapped to COM0. With value equal to 1, RAM row 1 is
        mapped to COM0 and so on.

        :param start_line:  Set display RAM display start line register from 0-63.
                            Display start line register is reset to 000000b during RESET.
        """
        self.check_int(start_line, 0, 0x3f)
        self.__oled_start_line = start_line
        self.__send_command([0x40 | start_line])

    def set_segment_remap(self, remap):
        """
        Set Segment Re-map (A0h/A1h)

        This command changes the mapping between the display data column address and the segment driver. It allows
        flexibility in OLED module design. Please refer to Table 9-1.

        This command only affects subsequent data input.  Data already stored in GDDRAM will have no changes.

        :param remap:   True - column address 127 is mapped to SEG0
                        False - column address 0 is mapped to SEG0 (RESET)
        """
        self.__send_command([0xa0 | remap])

    def set_multiplex_ratio(self, ratio):
        """
        Set Multiplex Ratio (A8h)

        This command switches the default 63 multiplex mode to any multiplex ratio, ranging from 16 to 63. The output
        pads COM0~COM63 will be switched to the corresponding COM signal.

        :param ratio:   Set MUX ratio to N+1 MUX
                        N=A[5:0] : from 16MUX to 64MUX,
                        RESET= 111111b (i.e. 63d, 64MUX)
                        A[5:0] from 0 to 14 are invalid entry.
        """
        self.check_int(ratio, 15, 63)
        self.__oled_mux_ratio = ratio
        self.__send_command([0xa8, ratio])

    def set_scan_direction(self, remapped):
        """
        Set COM Output Scan Direction (C0h/C8h)

        This command sets the scan direction of the COM output allowing layout flexibility in the OLED module design.
        Additionally, the display will show once this command is issued. For example, if this command is sent during
        normal display then the graphic display will be vertically flipped immediately.

        :param remapped:    True - remapped mode. Scan from COM[N-1] to COM0
                            False - normal mode. Scan from COM0 to COM[N –1] (RESET)
                            Where N is the Multiplex ratio.
        """
        self.check_int(remapped, 0, 1)
        self.__send_command([0xc0 | (remapped << 3)])

    def set_display_offset(self, offset):
        """
         Set Display Offset (D3h)

         This is a double byte command. The second command specifies the mapping of the display start line to one of
         COM0~COM63 (assuming that COM0 is the display start line then the display start line register is equal to 0).
         For example, to move the COM16 towards the COM0 direction by 16 lines the 6-bit data in the second byte should
         be given as 010000b. To move in the opposite direction by 16 lines the 6-bit data should be given by 64 – 16,
         so the second byte would be 100000b.

        :param offset:  Set vertical shift by COM from 0d~63d
                        The value is reset to 00h after RESET.
        """
        self.check_int(offset, 0, 63)
        self.__send_command([0xd3, offset])

    def set_com_pins_configuration(self, configuration, remap):
        """
        Set COM Pins Hardware Configuration (DAh)

        This command sets the COM signals pin configuration to match the OLED panel hardware layout.
        Refer to datasheet section 10.1.18 for detailed information.

        :param configuration:   0 - Sequential COM pin configuration,
                                1 - Alternative COM pin configuration (RESET)
        :param remap:   0 - Disable COM Left/Right remap (RESET)
                        1 - Enable COM Left/Right remap
        """
        self.check_int(configuration, 0, 1)
        self.check_int(remap, 0, 1)
        self.__send_command([0xda, 0x02 | (configuration << 4) | (remap << 5)])

    # 5. Timing & Driving Scheme Setting Command Table
    def set_display_clock(self, divider, osc_freq):

        """
        Set Display Clock Divide Ratio/Oscillator Frequency (D5h)

        This command consists of two functions:

            • Display Clock Divide Ratio (D)(A[3:0])

            Set the divide ratio to generate DCLK (Display Clock) from CLK.  The divide ratio is from 1 to 16, with
            reset value = 1.  Please refer to section 8.3 for the details relationship of DCLK and CLK.

            • Oscillator Frequency (A[7:4])

            Program the oscillator frequency Fosc that is the source of CLK if CLS pin is pulled high.  The 4-bit value
            results in 16 different frequency settings available as shown below.  The default setting is 1000b.

        :param divider: Define the divide ratio (D) of the display clocks (DCLK):
                        Dvide ration = DIVIDER + 1, RESET is 0 (divide ratio = 1)
        :param osc_freq: Set the Oscillator Frequncy, Fosc.
                         Oscillator Frequency increases with the value of OSC_FREQ and vice versa.
                         RESET is 1000b. Range: 0000b ~ 1111b.
        """
        self.check_int(divider, 0, 0xf)
        self.check_int(osc_freq, 0, 0xf)
        self.__send_command([0xd5, (osc_freq << 4 | divider)])

    def set_precharge_period(self, phase1, phase2):
        """
        Set Pre-charge Period (D9h)

        This command is used to set the duration of the pre-charge period. The interval is counted in number of DCLK,
        where RESET equals 2 DCLKs.

        :param phase1: Phase 1 period of up to 15 DCLK clocks, 0 is invalid entry (RESET = 2h)
        :param phase2: Phase 2 period of up to 15 DCLK clocks, 0 is invalid entry (RESET = 2h)
        """
        self.check_int(phase1, 1, 0xf)
        self.check_int(phase2, 1, 0xf)
        self.__send_command([0xd9, (phase2 << 4 | phase1)])

    def set_deselect_level(self, level):
        """
        Set Vcomh deselect level (DBh)

        This command adjust the Vcomh regulator output.

        :param level: 0, 1 or 2
                    0 ~ 0.65 * Vcc
                    1 ~ 0.77 * Vcc (RESET)
                    2 ~ 0.83 * Vcc
        """
        self.check_int(level, 0, 2)
        if level:
            level += 1
        self.__send_command([0xdb, level << 4])

    def send_nop(self):
        """
        NOP (E3h)

        No operation command
        """
        self.__send_command([0xe3])

    # 6. Charge Pump Command Table
    def charge_pump_setting(self, on):
        """
        Charge Pump Regulator (8Dh)

        :param on:  True - Enable charge pump during display on
                    False - Disable charge pump(RESET)
        """
        self.check_int(on, 0, 1)
        self.__send_command([0x8d, 0x10 | (on << 2)])





