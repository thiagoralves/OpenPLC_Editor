#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard.
# This files implements the bacnet plugin for Beremiz, adding BACnet server support.
#
# Copyright (C) 2017: Mario de Sousa (msousa@fe.up.pt)
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import
from collections import Counter

import wx

# Import some libraries on Beremiz code
from util.BitmapLibrary import GetBitmap
from controls.CustomGrid import CustomGrid
from controls.CustomTable import CustomTable
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor
from graphics.GraphicCommons import ERROR_HIGHLIGHT


# BACnet Engineering units taken from: ASHRAE 135-2016, clause/chapter 21
BACnetEngineeringUnits = [
    ('(Acceleration) meters-per-second-per-second (166)',              166),
    ('(Area) square-meters (0)',                                       0),
    ('(Area) square-centimeters (116)',                                116),
    ('(Area) square-feet (1)',                                         1),
    ('(Area) square-inches (115)',                                     115),
    ('(Currency) currency1 (105)',                                     105),
    ('(Currency) currency2 (106)',                                     106),
    ('(Currency) currency3 (107)',                                     107),
    ('(Currency) currency4 (108)',                                     108),
    ('(Currency) currency5 (109)',                                     109),
    ('(Currency) currency6 (110)',                                     110),
    ('(Currency) currency7 (111)',                                     111),
    ('(Currency) currency8 (112)',                                     112),
    ('(Currency) currency9 (113)',                                     113),
    ('(Currency) currency10 (114)',                                    114),
    ('(Electrical) milliamperes (2)',                                  2),
    ('(Electrical) amperes (3)',                                       3),
    ('(Electrical) amperes-per-meter (167)',                           167),
    ('(Electrical) amperes-per-square-meter (168)',                    168),
    ('(Electrical) ampere-square-meters (169)',                        169),
    ('(Electrical) decibels (199)',                                    199),
    ('(Electrical) decibels-millivolt (200)',                          200),
    ('(Electrical) decibels-volt (201)',                               201),
    ('(Electrical) farads (170)',                                      170),
    ('(Electrical) henrys (171)',                                      171),
    ('(Electrical) ohms (4)',                                          4),
    ('(Electrical) ohm-meter-squared-per-meter (237)',                 237),
    ('(Electrical) ohm-meters (172)',                                  172),
    ('(Electrical) milliohms (145)',                                   145),
    ('(Electrical) kilohms (122)',                                     122),
    ('(Electrical) megohms (123)',                                     123),
    ('(Electrical) microsiemens (190)',                                190),
    ('(Electrical) millisiemens (202)',                                202),
    ('(Electrical) siemens (173)',                                     173),
    ('(Electrical) siemens-per-meter (174)',                           174),
    ('(Electrical) teslas (175)',                                      175),
    ('(Electrical) volts (5)',                                         5),
    ('(Electrical) millivolts (124)',                                  124),
    ('(Electrical) kilovolts (6)',                                     6),
    ('(Electrical) megavolts (7)',                                     7),
    ('(Electrical) volt-amperes (8)',                                  8),
    ('(Electrical) kilovolt-amperes (9)',                              9),
    ('(Electrical) megavolt-amperes (10)',                             10),
    ('(Electrical) volt-amperes-reactive (11)',                        11),
    ('(Electrical) kilovolt-amperes-reactive (12)',                    12),
    ('(Electrical) megavolt-amperes-reactive (13)',                    13),
    ('(Electrical) volts-per-degree-kelvin (176)',                     176),
    ('(Electrical) volts-per-meter (177)',                             177),
    ('(Electrical) degrees-phase (14)',                                14),
    ('(Electrical) power-factor (15)',                                 15),
    ('(Electrical) webers (178)',                                      178),
    ('(Energy) ampere-seconds (238)',                                  238),
    ('(Energy) volt-ampere-hours (239)',                               239),
    ('(Energy) kilovolt-ampere-hours (240)',                           240),
    ('(Energy) megavolt-ampere-hours (241)',                           241),
    ('(Energy) volt-ampere-hours-reactive (242)',                      242),
    ('(Energy) kilovolt-ampere-hours-reactive (243)',                  243),
    ('(Energy) megavolt-ampere-hours-reactive (244)',                  244),
    ('(Energy) volt-square-hours (245)',                               245),
    ('(Energy) ampere-square-hours (246)',                             246),
    ('(Energy) joules (16)',                                           16),
    ('(Energy) kilojoules (17)',                                       17),
    ('(Energy) kilojoules-per-kilogram (125)',                         125),
    ('(Energy) megajoules (126)',                                      126),
    ('(Energy) watt-hours (18)',                                       18),
    ('(Energy) kilowatt-hours (19)',                                   19),
    ('(Energy) megawatt-hours (146)',                                  146),
    ('(Energy) watt-hours-reactive (203)',                             203),
    ('(Energy) kilowatt-hours-reactive (204)',                         204),
    ('(Energy) megawatt-hours-reactive (205)',                         205),
    ('(Energy) btus (20)',                                             20),
    ('(Energy) kilo-btus (147)',                                       147),
    ('(Energy) mega-btus (148)',                                       148),
    ('(Energy) therms (21)',                                           21),
    ('(Energy) ton-hours (22)',                                        22),
    ('(Enthalpy) joules-per-kilogram-dry-air (23)',                    23),
    ('(Enthalpy) kilojoules-per-kilogram-dry-air (149)',               149),
    ('(Enthalpy) megajoules-per-kilogram-dry-air (150)',               150),
    ('(Enthalpy) btus-per-pound-dry-air (24)',                         24),
    ('(Enthalpy) btus-per-pound (117)',                                117),
    ('(Entropy) joules-per-degree-kelvin (127)',                       127),
    ('(Entropy) kilojoules-per-degree-kelvin (151)',                   151),
    ('(Entropy) megajoules-per-degree-kelvin (152)',                   152),
    ('(Entropy) joules-per-kilogram-degree-kelvin (128)',              128),
    ('(Force) newton (153)',                                           153),
    ('(Frequency) cycles-per-hour (25)',                               25),
    ('(Frequency) cycles-per-minute (26)',                             26),
    ('(Frequency) hertz (27)',                                         27),
    ('(Frequency) kilohertz (129)',                                    129),
    ('(Frequency) megahertz (130)',                                    130),
    ('(Frequency) per-hour (131)',                                     131),
    ('(Humidity) grams-of-water-per-kilogram-dry-air (28)',            28),
    ('(Humidity) percent-relative-humidity (29)',                      29),
    ('(Length) micrometers (194)',                                     194),
    ('(Length) millimeters (30)',                                      30),
    ('(Length) centimeters (118)',                                     118),
    ('(Length) kilometers (193)',                                      193),
    ('(Length) meters (31)',                                           31),
    ('(Length) inches (32)',                                           32),
    ('(Length) feet (33)',                                             33),
    ('(Light) candelas (179)',                                         179),
    ('(Light) candelas-per-square-meter (180)',                        180),
    ('(Light) watts-per-square-foot (34)',                             34),
    ('(Light) watts-per-square-meter (35)',                            35),
    ('(Light) lumens (36)',                                            36),
    ('(Light) luxes (37)',                                             37),
    ('(Light) foot-candles (38)',                                      38),
    ('(Mass) milligrams (196)',                                        196),
    ('(Mass) grams (195)',                                             195),
    ('(Mass) kilograms (39)',                                          39),
    ('(Mass) pounds-mass (40)',                                        40),
    ('(Mass) tons (41)',                                               41),
    ('(Mass Flow) grams-per-second (154)',                             154),
    ('(Mass Flow) grams-per-minute (155)',                             155),
    ('(Mass Flow) kilograms-per-second (42)',                          42),
    ('(Mass Flow) kilograms-per-minute (43)',                          43),
    ('(Mass Flow) kilograms-per-hour (44)',                            44),
    ('(Mass Flow) pounds-mass-per-second (119)',                       119),
    ('(Mass Flow) pounds-mass-per-minute (45)',                        45),
    ('(Mass Flow) pounds-mass-per-hour (46)',                          46),
    ('(Mass Flow) tons-per-hour (156)',                                156),
    ('(Power) milliwatts (132)',                                       132),
    ('(Power) watts (47)',                                             47),
    ('(Power) kilowatts (48)',                                         48),
    ('(Power) megawatts (49)',                                         49),
    ('(Power) btus-per-hour (50)',                                     50),
    ('(Power) kilo-btus-per-hour (157)',                               157),
    ('(Power) joule-per-hours (247)',                                  247),
    ('(Power) horsepower (51)',                                        51),
    ('(Power) tons-refrigeration (52)',                                52),
    ('(Pressure) pascals (53)',                                        53),
    ('(Pressure) hectopascals (133)',                                  133),
    ('(Pressure) kilopascals (54)',                                    54),
    ('(Pressure) millibars (134)',                                     134),
    ('(Pressure) bars (55)',                                           55),
    ('(Pressure) pounds-force-per-square-inch (56)',                   56),
    ('(Pressure) millimeters-of-water (206)',                          206),
    ('(Pressure) centimeters-of-water (57)',                           57),
    ('(Pressure) inches-of-water (58)',                                58),
    ('(Pressure) millimeters-of-mercury (59)',                         59),
    ('(Pressure) centimeters-of-mercury (60)',                         60),
    ('(Pressure) inches-of-mercury (61)',                              61),
    ('(Temperature) degrees-celsius (62)',                             62),
    ('(Temperature) degrees-kelvin (63)',                              63),
    ('(Temperature) degrees-kelvin-per-hour (181)',                    181),
    ('(Temperature) degrees-kelvin-per-minute (182)',                  182),
    ('(Temperature) degrees-fahrenheit (64)',                          64),
    ('(Temperature) degree-days-celsius (65)',                         65),
    ('(Temperature) degree-days-fahrenheit (66)',                      66),
    ('(Temperature) delta-degrees-fahrenheit (120)',                   120),
    ('(Temperature) delta-degrees-kelvin (121)',                       121),
    ('(Time) years (67)',                                              67),
    ('(Time) months (68)',                                             68),
    ('(Time) weeks (69)',                                              69),
    ('(Time) days (70)',                                               70),
    ('(Time) hours (71)',                                              71),
    ('(Time) minutes (72)',                                            72),
    ('(Time) seconds (73)',                                            73),
    ('(Time) hundredths-seconds (158)',                                158),
    ('(Time) milliseconds (159)',                                      159),
    ('(Torque) newton-meters (160)',                                   160),
    ('(Velocity) millimeters-per-second (161)',                        161),
    ('(Velocity) millimeters-per-minute (162)',                        162),
    ('(Velocity) meters-per-second (74)',                              74),
    ('(Velocity) meters-per-minute (163)',                             163),
    ('(Velocity) meters-per-hour (164)',                               164),
    ('(Velocity) kilometers-per-hour (75)',                            75),
    ('(Velocity) feet-per-second (76)',                                76),
    ('(Velocity) feet-per-minute (77)',                                77),
    ('(Velocity) miles-per-hour (78)',                                 78),
    ('(Volume) cubic-feet (79)',                                       79),
    ('(Volume) cubic-meters (80)',                                     80),
    ('(Volume) imperial-gallons (81)',                                 81),
    ('(Volume) milliliters (197)',                                     197),
    ('(Volume) liters (82)',                                           82),
    ('(Volume) us-gallons (83)',                                       83),
    ('(Volumetric Flow) cubic-feet-per-second (142)',                  142),
    ('(Volumetric Flow) cubic-feet-per-minute (84)',                   84),
    ('(Volumetric Flow) million-standard-cubic-feet-per-minute (254)', 254),
    ('(Volumetric Flow) cubic-feet-per-hour (191)',                    191),
    ('(Volumetric Flow) cubic-feet-per-day (248)',                     248),
    ('(Volumetric Flow) standard-cubic-feet-per-day (47808)',          47808),
    ('(Volumetric Flow) million-standard-cubic-feet-per-day (47809)',  47809),
    ('(Volumetric Flow) thousand-cubic-feet-per-day (47810)',          47810),
    ('(Volumetric Flow) thousand-standard-cubic-feet-per-day (47811)', 47811),
    ('(Volumetric Flow) pounds-mass-per-day (47812)',                  47812),
    ('(Volumetric Flow) cubic-meters-per-second (85)',                 85),
    ('(Volumetric Flow) cubic-meters-per-minute (165)',                165),
    ('(Volumetric Flow) cubic-meters-per-hour (135)',                  135),
    ('(Volumetric Flow) cubic-meters-per-day (249)',                   249),
    ('(Volumetric Flow) imperial-gallons-per-minute (86)',             86),
    ('(Volumetric Flow) milliliters-per-second (198)',                 198),
    ('(Volumetric Flow) liters-per-second (87)',                       87),
    ('(Volumetric Flow) liters-per-minute (88)',                       88),
    ('(Volumetric Flow) liters-per-hour (136)',                        136),
    ('(Volumetric Flow) us-gallons-per-minute (89)',                   89),
    ('(Volumetric Flow) us-gallons-per-hour (192)',                    192),
    ('(Other) degrees-angular (90)',                                   90),
    ('(Other) degrees-celsius-per-hour (91)',                          91),
    ('(Other) degrees-celsius-per-minute (92)',                        92),
    ('(Other) degrees-fahrenheit-per-hour (93)',                       93),
    ('(Other) degrees-fahrenheit-per-minute (94)',                     94),
    ('(Other) joule-seconds (183)',                                    183),
    ('(Other) kilograms-per-cubic-meter (186)',                        186),
    ('(Other) kilowatt-hours-per-square-meter (137)',                  137),
    ('(Other) kilowatt-hours-per-square-foot (138)',                   138),
    ('(Other) watt-hours-per-cubic-meter (250)',                       250),
    ('(Other) joules-per-cubic-meter (251)',                           251),
    ('(Other) megajoules-per-square-meter (139)',                      139),
    ('(Other) megajoules-per-square-foot (140)',                       140),
    ('(Other) mole-percent (252)',                                     252),
    ('(Other) no-units (95)',                                          95),
    ('(Other) newton-seconds (187)',                                   187),
    ('(Other) newtons-per-meter (188)',                                188),
    ('(Other) parts-per-million (96)',                                 96),
    ('(Other) parts-per-billion (97)',                                 97),
    ('(Other) pascal-seconds (253)',                                   253),
    ('(Other) percent (98)',                                           98),
    ('(Other) percent-obscuration-per-foot (143)',                     143),
    ('(Other) percent-obscuration-per-meter (144)',                    144),
    ('(Other) percent-per-second (99)',                                99),
    ('(Other) per-minute (100)',                                       100),
    ('(Other) per-second (101)',                                       101),
    ('(Other) psi-per-degree-fahrenheit (102)',                        102),
    ('(Other) radians (103)',                                          103),
    ('(Other) radians-per-second (184)',                               184),
    ('(Other) revolutions-per-minute (104)',                           104),
    ('(Other) square-meters-per-newton (185)',                         185),
    ('(Other) watts-per-meter-per-degree-kelvin (189)',                189),
    ('(Other) watts-per-square-meter-degree-kelvin (141)',             141),
    ('(Other) per-mille (207)',                                        207),
    ('(Other) grams-per-gram (208)',                                   208),
    ('(Other) kilograms-per-kilogram (209)',                           209),
    ('(Other) grams-per-kilogram (210)',                               210),
    ('(Other) milligrams-per-gram (211)',                              211),
    ('(Other) milligrams-per-kilogram (212)',                          212),
    ('(Other) grams-per-milliliter (213)',                             213),
    ('(Other) grams-per-liter (214)',                                  214),
    ('(Other) milligrams-per-liter (215)',                             215),
    ('(Other) micrograms-per-liter (216)',                             216),
    ('(Other) grams-per-cubic-meter (217)',                            217),
    ('(Other) milligrams-per-cubic-meter (218)',                       218),
    ('(Other) micrograms-per-cubic-meter (219)',                       219),
    ('(Other) nanograms-per-cubic-meter (220)',                        220),
    ('(Other) grams-per-cubic-centimeter (221)',                       221),
    ('(Other) becquerels (222)',                                       222),
    ('(Other) kilobecquerels (223)',                                   223),
    ('(Other) megabecquerels (224)',                                   224),
    ('(Other) gray (225)',                                             225),
    ('(Other) milligray (226)',                                        226),
    ('(Other) microgray (227)',                                        227),
    ('(Other) sieverts (228)',                                         228),
    ('(Other) millisieverts (229)',                                    229),
    ('(Other) microsieverts (230)',                                    230),
    ('(Other) microsieverts-per-hour (231)',                           231),
    ('(Other) millirems (47814)',                                      47814),
    ('(Other) millirems-per-hour (47815)',                             47815),
    ('(Other) decibels-a (232)',                                       232),
    ('(Other) nephelometric-turbidity-unit (233)',                     233),
    ('(Other) pH (234)',                                               234),
    ('(Other) grams-per-square-meter (235)',                           235),
    ('(Other) minutes-per-degree-kelvin (236)',                        236)
]  # BACnetEngineeringUnits


# ObjectID (22 bits ID + 10 bits type) => max = 2^22-1 = 4194303
#  However, ObjectID 4194303 is not allowed!
#  4194303 is used as a special value when object Id reference is referencing an undefined object
#  (similar to NULL in C)
BACnetObjectID_MAX = 4194302
BACnetObjectID_NUL = 4194303


# A base class
# what would be a purely virtual class in C++
class ObjectProperties(object):
    # this __init_() function is currently not beeing used!

    def __init__(self):
        # nothing to do
        return


class BinaryObject(ObjectProperties):
    # 'PropertyNames' will be used as the header for each column of the Object Properties grid!
    # Warning: The rest of the code depends on the existance of an "Object Identifier" and "Object Name"
    # Be sure to use these exact names for these BACnet object properties!
    PropertyNames = ["Object Identifier", "Object Name", "Description"]
    ColumnAlignments = [wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_LEFT]
    ColumnSizes = [40, 80, 80]
    PropertyConfig = {
        "Object Identifier": {"GridCellEditor": wx.grid.GridCellNumberEditor,
                              "GridCellRenderer": wx.grid.GridCellNumberRenderer,
                              # syntax for GridCellNumberEditor -> "min,max"
                              # ObjectID (22 bits ID + 10 bits type) => max = 2^22-1
                              "GridCellEditorParam": "0,4194302"},
        "Object Name": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer},
        "Description": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer}
    }


class AnalogObject(ObjectProperties):
    # 'PropertyNames' will be used as the header for each column of the Object Properties grid!
    # Warning: The rest of the code depends on the existance of an "Object Identifier" and "Object Name"
    #          Be sure to use these exact names for these BACnet object properties!
    #
    # NOTE: Although it is not listed here (so it does not show up in the GUI, this object will also
    #       keep another entry for a virtual property named "Unit ID". This virtual property
    #       will store the ID corresponding to the "Engineering Units" currently chosen.
    #       This virtual property is kept synchronised to the "Engineering Units" property
    #       by the function PropertyChanged() which should be called by the OnCellChange event handler.
    PropertyNames = ["Object Identifier", "Object Name",
                     "Description", "Engineering Units"]  # 'Unit ID'
    ColumnAlignments = [
        wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT]
    ColumnSizes = [40, 80, 80, 200]
    PropertyConfig = {
        "Object Identifier": {"GridCellEditor": wx.grid.GridCellNumberEditor,
                              "GridCellRenderer": wx.grid.GridCellNumberRenderer,
                              "GridCellEditorParam": "0,4194302"},
        "Object Name": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer},
        "Description": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer},
        "Engineering Units": {"GridCellEditor": wx.grid.GridCellChoiceEditor,
                              # use string renderer with choice editor!
                              "GridCellRenderer": wx.grid.GridCellStringRenderer,
                              # syntax for GridCellChoiceEditor -> comma separated values
                              "GridCellEditorParam": ','.join([x[0] for x in BACnetEngineeringUnits])}
    }

    # obj_properties should be a dictionary, with keys "Object Identifier",
    # "Object Name", "Description", ...
    def UpdateVirtualProperties(self, obj_properties):
        obj_properties["Unit ID"] = [x[1]
                                     for x in BACnetEngineeringUnits if x[0] == obj_properties["Engineering Units"]][0]


class MultiSObject(ObjectProperties):
    # 'PropertyNames' will be used as the header for each column of the Object Properties grid!
    # Warning: The rest of the code depends on the existance of an "Object Identifier" and "Object Name"
    # Be sure to use these exact names for these BACnet object properties!
    PropertyNames = [
        "Object Identifier", "Object Name", "Description", "Number of States"]
    ColumnAlignments = [
        wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_CENTER]
    ColumnSizes = [40, 80, 80, 120]
    PropertyConfig = {
        "Object Identifier": {"GridCellEditor": wx.grid.GridCellNumberEditor,
                              "GridCellRenderer": wx.grid.GridCellNumberRenderer,
                              "GridCellEditorParam": "0,4194302"},
        "Object Name": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer},
        "Description": {"GridCellEditor": wx.grid.GridCellTextEditor,
                        "GridCellRenderer": wx.grid.GridCellStringRenderer},
        # MultiState Values are encoded in unsigned integer
        # (in BACnet => uint8_t), and can not be 0.
        # See ASHRAE 135-2016, section 12.20.4
        "Number of States": {"GridCellEditor": wx.grid.GridCellNumberEditor,
                             "GridCellRenderer": wx.grid.GridCellNumberRenderer,
                             # syntax for GridCellNumberEditor -> "min,max"
                             "GridCellEditorParam": "1,255"}
    }


# The default values to use for each BACnet object type
#
# Note that the 'internal plugin parameters' get stored in the data table, but
# are not visible in the GUI. They are used to generate the
# EDE files as well as the C code
class BVObject(BinaryObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Binary Value",
                     "Description": "",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 5,
                     "Ctype": "uint8_t",
                     "Settable": "Y"}


class BOObject(BinaryObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Binary Output",
                     "Description": "",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 4,
                     "Ctype": "uint8_t",
                     "Settable": "Y"}


class BIObject(BinaryObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Binary Input",
                     "Description": "",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 3,
                     "Ctype": "uint8_t",
                     "Settable": "N"}


class AVObject(AnalogObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Analog Value",
                     "Description": "",
                     "Engineering Units": '(Other) no-units (95)',
                     # internal plugin parameters...
                     "Unit ID": 95,   # the ID of the engineering unit
                     # will get updated by
                     # UpdateVirtualProperties()
                     "BACnetObjTypeID": 2,
                     "Ctype": "float",
                     "Settable": "Y"}


class AOObject(AnalogObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Analog Output",
                     "Description": "",
                     "Engineering Units": '(Other) no-units (95)',
                     # internal plugin parameters...
                     "Unit ID": 95,   # the ID of the engineering unit
                     # will get updated by
                     # UpdateVirtualProperties()
                     "BACnetObjTypeID": 1,
                     "Ctype": "float",
                     "Settable": "Y"}


class AIObject(AnalogObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Analog Input",
                     "Description": "",
                     "Engineering Units": '(Other) no-units (95)',
                     # internal plugin parameters...
                     "Unit ID": 95,   # the ID of the engineering unit
                     # will get updated by
                     # UpdateVirtualProperties()
                     "BACnetObjTypeID": 0,
                     "Ctype": "float",
                     "Settable": "N"}


class MSVObject(MultiSObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Multi-state Value",
                     "Description": "",
                     "Number of States": "255",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 19,
                     "Ctype": "uint8_t",
                     "Settable": "Y"}


class MSOObject(MultiSObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Multi-state Output",
                     "Description": "",
                     "Number of States": "255",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 14,
                     "Ctype": "uint8_t",
                     "Settable": "Y"}


class MSIObject(MultiSObject):
    DefaultValues = {"Object Identifier": "",
                     "Object Name": "Multi-state Input",
                     "Description": "",
                     "Number of States": "255",
                     # internal plugin parameters...
                     "BACnetObjTypeID": 13,
                     "Ctype": "uint8_t",
                     "Settable": "N"}


class ObjectTable(CustomTable):
    #  A custom wx.grid.PyGridTableBase using user supplied data
    #
    #  This will basically store a list of BACnet objects that the slave will support/implement.
    #  There will be one instance of this ObjectTable class for each BACnet object type
    #  (e.g. Binary Value, Analog Input, Multi State Output, ...)
    #
    #  The list of BACnet objects will actually be stored within the self.data variable
    #  (declared in CustomTable). Self.data will be a list of dictionaries (one entry per BACnet
    #  object). All of these dictionaries in the self.data list will have entries whose keys actually
    #  depend on the BACnet type object being handled. The keys in the dictionary will be
    #  the entries in the PropertyNames list of one of the following classes:
    #  (BVObject, BOObject, BIObject, AVObject, AOObject, AIObject, MSVObject, MSOObject, MSIObject).
    #
    #  For example, when handling Binary Value BACnet objects,
    #   self.data will be a list of dictionaries (one entry per row)
    #     self.data[n] will be a dictionary, with keys "Object Identifier", "Object Name", "Description"
    #     for example: self.data[n] = {"Object Identifier":33, "Object Name":"room1", "Description":"xx"}
    #
    #  Note that this ObjectTable class merely stores the configuration data.
    #  It does not control the display nor the editing of this data.
    #  This data is typically displayed within a grid, that is controlled by the ObjectGrid class.
    #

    def __init__(self, parent, data, BACnetObjectType):
        #   parent          : the _BacnetSlavePlug object that is instantiating this ObjectTable
        #   data            : a list with the data to be shown on the grid
        #                       (i.e., a list containing the BACnet object properties)
        #                       Instantiated in _BacnetSlavePlug
        #   BACnetObjectType: one of BinaryObject, AnalogObject, MultiSObject
        #                     (or a class that derives from them).
        #                     This is actually the class itself, and not a variable!!!
        #                     However, self.BACnetObjectType will be an instance
        #                     of said class as we later need to call methods from this class.
        #                     (in particular, the UpdateVirtualProperties() method)
        #
        # The base class must be initialized *first*
        CustomTable.__init__(
            self, parent, data, BACnetObjectType.PropertyNames)
        self.BACnetObjectType = BACnetObjectType()
        self.ChangesToSave = False

    # def _GetRowEdit(self, row):
        # row_edit = self.GetValueByName(row, "Edit")
        # var_type = self.Parent.GetTagName()
        # bodytype = self.Parent.Controler.GetEditedElementBodyType(var_type)
        # if bodytype in ["ST", "IL"]:
        #     row_edit = True;
        # return row_edit

    def _updateColAttrs(self, grid):
        #  wx.grid.Grid -> update the column attributes to add the
        #  appropriate renderer given the column name.
        #
        #  Otherwise default to the default renderer.
        # print "ObjectTable._updateColAttrs() called!!!"
        for row in range(self.GetNumberRows()):
            for col in range(self.GetNumberCols()):
                PropertyName = self.BACnetObjectType.PropertyNames[col]
                PropertyConfig = self.BACnetObjectType.PropertyConfig[PropertyName]
                grid.SetReadOnly(row, col, False)
                grid.SetCellEditor(row, col, PropertyConfig["GridCellEditor"]())
                grid.SetCellRenderer(row, col, PropertyConfig["GridCellRenderer"]())
                grid.SetCellBackgroundColour(row, col, wx.WHITE)
                grid.SetCellTextColour(row, col, wx.BLACK)
                if "GridCellEditorParam" in PropertyConfig:
                    grid.GetCellEditor(row, col).SetParameters(
                        PropertyConfig["GridCellEditorParam"])
            self.ResizeRow(grid, row)

    def FindValueByName(self, PropertyName, PropertyValue):
        # find the row whose property named PropertyName has the value PropertyValue
        # Returns: row number
        # for example, find the row where PropertyName "Object Identifier" has value 1002
        #              FindValueByName("Object Identifier", 1002).
        for row in range(self.GetNumberRows()):
            if int(self.GetValueByName(row, PropertyName)) == PropertyValue:
                return row
        return None

    # Return a list containing all the values under the column named 'colname'
    def GetAllValuesByName(self, colname):
        values = []
        for row in range(self.GetNumberRows()):
            values.append(self.data[row].get(colname))
        return values

    # Returns a dictionary with:
    #      keys: IDs    of BACnet objects
    #     value: number of BACnet objects using this same Id
    #            (values larger than 1 indicates an error as BACnet requires unique
    #             object IDs for objects of the same type)
    def GetObjectIDCount(self):
        # The dictionary is built by first creating a list containing the IDs
        # of all BACnet objects
        ObjectIDs = self.GetAllValuesByName("Object Identifier")
        # list of integers instead of strings...
        ObjectIDs_as_int = [int(x) for x in ObjectIDs]
        # This list is then transformed into a collections.Counter class
        # Which is then transformed into a dictionary using dict()
        return dict(Counter(ObjectIDs_as_int))

    # Check whether any object ID is used more than once (not valid in BACnet)
    # (returns True or False)
    def HasDuplicateObjectIDs(self):
        ObjectIDsCount = self.GetObjectIDCount()
        for ObjName in ObjectIDsCount:
            if ObjectIDsCount[ObjName] > 1:
                return True
        return False

    # Update the virtual properties of the objects of the classes derived from ObjectProperties
    #  (currently only the AnalogObject class had virtua properties, i.e. a property
    #   that is determined/calculated based on the other properties)
    def UpdateAllVirtualProperties(self):
        if hasattr(self.BACnetObjectType, 'UpdateVirtualProperties'):
            for ObjProp in self.data:
                self.BACnetObjectType.UpdateVirtualProperties(ObjProp)


class ObjectGrid(CustomGrid):
    # A custom wx.grid.Grid (CustomGrid derives from wx.grid.Grid)
    #
    # Needed mostly to customise the initial values of newly added rows, and to
    # validate if the inserted data follows BACnet rules.
    #
    #
    # This ObjectGrid class:
    #   Creates and controls the GUI __grid__ for configuring all the BACnet objects of one
    #   (generic) BACnet object type (e.g. Binary Value, Analog Input, Multi State Output, ...)
    #   This grid is currently displayed within one 'window' controlled by a ObjectEditor
    #   object (this organization is not likely to change in the future).
    #
    #   The grid uses one line/row per BACnet object, and one column for each property of the BACnet
    #   object. The column titles change depending on the specific type of BACnet object being edited
    #   (BVObject, BOObject, BIObject, AVObject, AOObject, AIObject, MSVObject, MSOObject, MSIObject).
    #   The editor to use for each column is also obtained from that class (e.g. TextEditor,
    #   NumberEditor, ...)
    #
    #   This class does NOT store the data in the grid. It merely controls its display and editing.
    #   The data in the grid is stored within an object of class ObjectTable
    #

    def __init__(self, *args, **kwargs):
        CustomGrid.__init__(self, *args, **kwargs)

    # Called when a new row is added by clicking Add button
    # call graph: CustomGrid.OnAddButton() --> CustomGrid.AddRow() -->
    # ObjectGrid._AddRow()
    def _AddRow(self, new_row):
        if new_row > 0:
            self.Table.InsertRow(new_row, self.Table.GetRow(new_row - 1).copy())
        else:
            self.Table.InsertRow(new_row, self.DefaultValue.copy())
        # start off with invalid object ID
        self.Table.SetValueByName(new_row, "Object Identifier", BACnetObjectID_NUL)
        # Find an apropriate BACnet object ID for the new object.
        # We choose a first attempt (based on object ID of previous line + 1)
        new_object_id = 0
        if new_row > 0:
            new_object_id = int(
                self.Table.GetValueByName(new_row - 1, "Object Identifier"))
            new_object_id += 1
        # Check whether the chosen object ID is not already in use.
        # If in use, add 1 to the attempted object ID and recheck...
        while self.Table.FindValueByName("Object Identifier", new_object_id) is not None:
            new_object_id += 1
            # if reached end of object IDs, cycle back to 0
            # (remember, we may have started at any inital object ID > 0, so it makes sense to cyclce back to 0)
            # warning: We risk entering an inifinite loop if all object IDs are already used.
            #          The likelyhood of this happening is extremely low, (we would need 2^22 elements in the table!)
            #          so don't worry about it for now.
            if new_object_id > BACnetObjectID_MAX:
                new_object_id = 0
        # Set the object ID of the new object to the apropriate value
        # ... and append the ID to the default object name (so the name becomes unique)
        new_object_name = self.DefaultValue.get(
            "Object Name") + " " + str(new_object_id)
        self.Table.SetValueByName(
            new_row, "Object Name", new_object_name)
        self.Table.SetValueByName(new_row, "Object Identifier", new_object_id)
        self.Table.ResetView(self)
        return new_row

    # Called when a object ID is changed
    #    call graph: ObjectEditor.OnVariablesGridCellChange() --> this method
    # Will check whether there is a duplicate object ID, and highlight it if so.
    def HighlightDuplicateObjectIDs(self):
        if self.Table.GetNumberRows() < 2:
            # Less than 2 rows. No duplicates are possible!
            return
        IDsCount = self.Table.GetObjectIDCount()
        # check ALL object IDs for duplicates...
        for row in range(self.Table.GetNumberRows()):
            obj_id1 = int(self.Table.GetValueByName(row, "Object Identifier"))
            if IDsCount[obj_id1] > 1:
                # More than 1 BACnet object using this ID! Let us Highlight this row with errors...
                # TODO: change the hardcoded column number '0' to a number obtained at runtime
                #       that is guaranteed to match the column titled "Object Identifier"
                self.SetCellBackgroundColour(row, 0, ERROR_HIGHLIGHT[0])
                self.SetCellTextColour(row, 0, ERROR_HIGHLIGHT[1])
            else:
                self.SetCellBackgroundColour(row, 0, wx.WHITE)
                self.SetCellTextColour(row, 0, wx.BLACK)
        # Refresh the graphical display to take into account any changes we may
        # have made
        self.ForceRefresh()
        return None

    # Called when the user changes the name of BACnet object (using the GUI grid)
    #    call graph: ObjectEditor.OnVariablesGridCellChange() -->
    #                --> BacnetSlaveEditorPlug.HighlightAllDuplicateObjectNames() -->
    #                --> ObjectEditor.HighlightDuplicateObjectNames() -->
    #                -->   (this method)
    # Will check whether there is a duplicate BACnet object name, and highlight it if so.
    #
    # Since the names of BACnet objects must be unique within the whole bacnet server (and
    # not just among the BACnet objects of the same class (e.g. Analog Value, Binary Input, ...)
    # to work properly this method must be passed a list of the names of all BACnet objects
    # currently configured.
    #
    # AllObjectNamesFreq: a dictionary using as key the names of all currently configured BACnet
    #                     objects, and value the number of objects using this same name.
    def HighlightDuplicateObjectNames(self, AllObjectNamesFreq):
        for row in range(self.Table.GetNumberRows()):
            # TODO: change the hardcoded column number '1' to a number obtained at runtime
            #       that is guaranteed to match the column titled "Object Name"
            if AllObjectNamesFreq[self.Table.GetValueByName(row, "Object Name")] > 1:
                # This is an error! Highlight it...
                self.SetCellBackgroundColour(row, 1, ERROR_HIGHLIGHT[0])
                self.SetCellTextColour(row, 1, ERROR_HIGHLIGHT[1])
            else:
                self.SetCellBackgroundColour(row, 1, wx.WHITE)
                self.SetCellTextColour(row, 1, wx.BLACK)
        # Refresh the graphical display to take into account any changes we may
        # have made
        self.ForceRefresh()
        return None


class ObjectEditor(wx.Panel):
    # This ObjectEditor class:
    #   Creates and controls the GUI window for configuring all the BACnet objects of one
    #   (generic) BACnet object type (e.g. Binary Value, Analog Input, Multi State Output, ...)
    #   This 'window' is currenty displayed within one tab of the bacnet plugin, but this
    #   may change in the future!
    #
    #   It includes a grid to display all the BACnet objects of its type , as well as the buttons
    #   to insert, delete and move (up/down) a BACnet object in the grid.
    #   It also includes the sizers and spacers required to lay out the grid and buttons
    #   in the wndow.
    #

    def __init__(self, parent, window, controller, ObjTable):
        # window:  the window in which the editor will open.
        # controller: The ConfigTreeNode object that controlls the data presented by
        #             this 'config tree node editor'
        #
        # parent:  wx._controls.Notebook
        # window:  BacnetSlaveEditorPlug (i.e. beremiz.bacnet.BacnetSlaveEditor.BacnetSlaveEditorPlug)
        # controller: controller will be an object of class
        #            FinalCTNClass         (i.e. beremiz.ConfigTreeNode.FinalCTNClass )
        #            (FinalCTNClass inherits from: ConfigTreeNode and _BacnetSlavePlug)
        #            (For the BACnet plugin, it is easier to think of controller as a _BacnetSlavePlug,
        #             as the other classes are generic to all plugins!!)
        #
        # ObjTable: The object of class ObjectTable that stores the data displayed in the grid.
        #           This object is instantiated and managed by the _BacnetSlavePlug class.
        #
        self.window = window
        self.controller = controller
        self.ObjTable = ObjTable

        wx.Panel.__init__(self, parent)

        # The main sizer, 2 rows: top row for buttons, bottom row for 2D grid
        self.MainSizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=0)
        self.MainSizer.AddGrowableCol(0)
        self.MainSizer.AddGrowableRow(1)

        # sizer placed on top row of main sizer:
        #   1 row; 6 columns: 1 static text, one stretchable spacer, 4 buttons
        controls_sizer = wx.FlexGridSizer(cols=6, hgap=4, rows=1, vgap=5)
        controls_sizer.AddGrowableCol(0)
        controls_sizer.AddGrowableRow(0)
        self.MainSizer.Add(controls_sizer, border=5, flag=wx.GROW | wx.ALL)

        # the buttons that populate the controls sizer (itself in top row of the main sizer)
        # NOTE: the _("string") function will translate the "string" to the local language
        controls_sizer.Add(
            wx.StaticText(self, label=_('Object Properties:')), flag=wx.ALIGN_BOTTOM)
        controls_sizer.AddStretchSpacer()
        for name, bitmap, help in [
                ("AddButton", "add_element", _("Add variable")),
                ("DeleteButton", "remove_element", _("Remove variable")),
                ("UpButton", "up", _("Move variable up")),
                ("DownButton", "down", _("Move variable down"))]:
            button = wx.lib.buttons.GenBitmapButton(
                self, bitmap=GetBitmap(bitmap),
                size=wx.Size(28, 28),
                style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            controls_sizer.Add(button)

        # the variable grid that will populate the bottom row of the main sizer
        panel = self
        self.VariablesGrid = ObjectGrid(panel, style=wx.VSCROLL)
        # use only to enable drag'n'drop
        # self.VariablesGrid.SetDropTarget(VariableDropTarget(self))
        self.VariablesGrid.Bind(
            wx.grid.EVT_GRID_CELL_CHANGE,     self.OnVariablesGridCellChange)
        # self.VariablesGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnVariablesGridCellLeftClick)
        # self.VariablesGrid.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,    self.OnVariablesGridEditorShown)
        self.MainSizer.Add(self.VariablesGrid, flag=wx.GROW)

        # Configure the Variables Grid...
        # do not include a leftmost column containing the 'row label'
        self.VariablesGrid.SetRowLabelSize(0)
        self.VariablesGrid.SetButtons({"Add":    self.AddButton,
                                       "Delete": self.DeleteButton,
                                       "Up":     self.UpButton,
                                       "Down":   self.DownButton})
        # The custom grid needs to know the default values to use when 'AddButton' creates a new row
        # NOTE: ObjTable.BACnetObjectType will contain the class name of one of the following classes
        # (BVObject, BIObject, BOObject, AVObject, AIObject, AOObject, MSVObject, MSIObject, MSOObject)
        # which inherit from one of (BinaryObject, AnalogObject, MultiSObject)
        self.VariablesGrid.SetDefaultValue(
            self.ObjTable.BACnetObjectType.DefaultValues)

        # self.ObjTable: The table that contains the data displayed in the grid
        # This table was instantiated/created in the initializer for class _BacnetSlavePlug
        self.VariablesGrid.SetTable(self.ObjTable)
        self.VariablesGrid.SetEditable(True)
        # set the column attributes (width, alignment)
        # NOTE: ObjTable.BACnetObjectType will contain the class name of one of the following classes
        # (BVObject, BIObject, BOObject, AVObject, AIObject, AOObject, MSVObject, MSIObject, MSOObject)
        # which inherit from one of (BinaryObject, AnalogObject, MultiSObject)
        ColumnAlignments = self.ObjTable.BACnetObjectType.ColumnAlignments
        ColumnSizes = self.ObjTable.BACnetObjectType.ColumnSizes
        for col in range(self.ObjTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(ColumnAlignments[col], wx.ALIGN_CENTRE)
            self.VariablesGrid.SetColAttr(col, attr)
            self.VariablesGrid.SetColMinimalWidth(col, ColumnSizes[col])
            self.VariablesGrid.AutoSizeColumn(col, False)

        # layout the items in all sizers, and show them too.
        self.SetSizer(self.MainSizer)    # Have the wondow 'own' the sizer...
        # self.MainSizer.ShowItems(True)  # not needed once the window 'owns' the sizer (SetSizer())
        # self.MainSizer.Layout()         # not needed once the window 'owns' the sizer (SetSizer())

        # Refresh the view of the grid...
        #   We ask the table to do that, who in turn will configure the grid for us!!
        #   It will configure the CellRenderers and CellEditors taking into account the type of
        #   BACnet object being shown in the grid!!
        #
        #   Yes, I (Mario de Sousa) know this architecture does not seem to make much sense.
        #   It seems to me that the cell renderers etc. should all be configured right here.
        #   Unfortunately we inherit from the customTable and customGrid classes in Beremiz
        #   (in order to maintain GUI consistency), so we have to adopt their way of doing things.
        #
        # NOTE: ObjectTable.ResetView() (remember, ObjTable is of class ObjectTable)
        #         calls ObjectTable._updateColAttrs(), who will do the configuring.
        self.ObjTable.ResetView(self.VariablesGrid)

    def RefreshView(self):
        # print "ObjectEditor.RefreshView() called!!!"
        # Check for Duplicate Object IDs is only done within same BACnet object type (ID is unique by type).
        # The VariablesGrid class can handle it by itself.
        self.VariablesGrid.HighlightDuplicateObjectIDs()
        # Check for Duplicate Object Names must be done globally (Object Name is unique within bacnet server)
        # Only the BacnetSlaveEditorPlug can and will handle this.
        # self.window.HighlightAllDuplicateObjectNames()

    #
    # Event handlers for the Variables Grid #
    #
    def OnVariablesGridCellChange(self, event):
        col = event.GetCol()
        # print "ObjectEditor.OnVariablesGridCellChange(row=%s, col=%s)
        # called!!!" % (row, col)
        self.ObjTable.ChangesToSave = True
        if self.ObjTable.GetColLabelValue(col) == "Object Identifier":
            # an Object ID was changed => must check duplicate object IDs.
            self.VariablesGrid.HighlightDuplicateObjectIDs()
        if self.ObjTable.GetColLabelValue(col) == "Object Name":
            # an Object Name was changed => must check duplicate object names.
            # Note that this must be done to _all_ BACnet objects, and not just the objects
            # of the same BACnet class (Binary Value, Analog Input, ...)
            # So we have the BacnetSlaveEditorPlug class do it...
            self.window.HighlightAllDuplicateObjectNames()
        # There are changes to save =>
        # udate the enabled/disabled state of the 'save' option in the 'file' menu
        self.window.RefreshBeremizWindow()
        event.Skip()

    def OnVariablesGridCellLeftClick(self, event):
        pass

    def OnVariablesGridEditorShown(self, event):
        pass

    def HighlightDuplicateObjectNames(self, AllObjectNamesFreq):
        return self.VariablesGrid.HighlightDuplicateObjectNames(AllObjectNamesFreq)


class BacnetSlaveEditorPlug(ConfTreeNodeEditor):
    # inheritance tree
    #  wx.SplitterWindow-->EditorPanel-->ConfTreeNodeEditor-->BacnetSlaveEditorPlug
    #
    # self.Controller -> The object that controls the data displayed in this editor
    #                    In our case, the object of class _BacnetSlavePlug

    CONFNODEEDITOR_TABS = [
        (_("Analog Value Objects"),       "_create_AV_ObjectEditor"),
        (_("Analog Output Objects"),      "_create_AO_ObjectEditor"),
        (_("Analog Input Objects"),       "_create_AI_ObjectEditor"),
        (_("Binary Value Objects"),       "_create_BV_ObjectEditor"),
        (_("Binary Output Objects"),      "_create_BO_ObjectEditor"),
        (_("Binary Input Objects"),       "_create_BI_ObjectEditor"),
        (_("Multi-State Value Objects"),  "_create_MSV_ObjectEditor"),
        (_("Multi-State Output Objects"), "_create_MSO_ObjectEditor"),
        (_("Multi-State Input Objects"), "_create_MSI_ObjectEditor")]

    def _create_AV_ObjectEditor(self, parent):
        self.AV_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["AV_Obj"])
        return self.AV_ObjectEditor

    def _create_AO_ObjectEditor(self, parent):
        self.AO_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["AO_Obj"])
        return self.AO_ObjectEditor

    def _create_AI_ObjectEditor(self, parent):
        self.AI_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["AI_Obj"])
        return self.AI_ObjectEditor

    def _create_BV_ObjectEditor(self, parent):
        self.BV_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["BV_Obj"])
        return self.BV_ObjectEditor

    def _create_BO_ObjectEditor(self, parent):
        self.BO_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["BO_Obj"])
        return self.BO_ObjectEditor

    def _create_BI_ObjectEditor(self, parent):
        self.BI_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["BI_Obj"])
        return self.BI_ObjectEditor

    def _create_MSV_ObjectEditor(self, parent):
        self.MSV_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["MSV_Obj"])
        return self.MSV_ObjectEditor

    def _create_MSO_ObjectEditor(self, parent):
        self.MSO_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["MSO_Obj"])
        return self.MSO_ObjectEditor

    def _create_MSI_ObjectEditor(self, parent):
        self.MSI_ObjectEditor = ObjectEditor(
            parent, self, self.Controler, self.Controler.ObjTables["MSI_Obj"])
        return self.MSI_ObjectEditor

    def __init__(self, parent, controler, window, editable=True):
        self.Editable = editable
        ConfTreeNodeEditor.__init__(self, parent, controler, window)

    def __del__(self):
        self.Controler.OnCloseEditor(self)

    def GetConfNodeMenuItems(self):
        return []

    def RefreshConfNodeMenu(self, confnode_menu):
        return

    def RefreshView(self):
        self.HighlightAllDuplicateObjectNames()
        ConfTreeNodeEditor.RefreshView(self)
        self. AV_ObjectEditor.RefreshView()
        self. AO_ObjectEditor.RefreshView()
        self. AI_ObjectEditor.RefreshView()
        self. BV_ObjectEditor.RefreshView()
        self. BO_ObjectEditor.RefreshView()
        self. BI_ObjectEditor.RefreshView()
        self.MSV_ObjectEditor.RefreshView()
        self.MSO_ObjectEditor.RefreshView()
        self.MSI_ObjectEditor.RefreshView()

    def HighlightAllDuplicateObjectNames(self):
        ObjectNamesCount = self.Controler.GetObjectNamesCount()
        self. AV_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self. AO_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self. AI_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self. BV_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self. BO_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self. BI_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self.MSV_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self.MSO_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        self.MSI_ObjectEditor.HighlightDuplicateObjectNames(ObjectNamesCount)
        return None

    def RefreshBeremizWindow(self):
        # self.ParentWindow is the top level Beremiz class (object) that
        #                   handles the beremiz window and layout

        # Refresh the title of the Beremiz window
        #  (it changes depending on whether there are
        #   changes to save!! )
        self.ParentWindow.RefreshTitle()

        # Refresh the enabled/disabled state of the
        #  entries in the main 'file' menu.
        #  ('Save' sub-menu should become enabled
        #   if there are changes to save! )
        self.ParentWindow.RefreshFileMenu()

        # self.ParentWindow.RefreshEditMenu()
        # self.ParentWindow.RefreshPageTitles()
