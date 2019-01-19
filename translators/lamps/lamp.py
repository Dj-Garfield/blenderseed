#
# This source file is part of appleseed.
# Visit http://appleseedhq.net/ for additional information and resources.
#
# This software is released under the MIT license.
#
# Copyright (c) 2019 The appleseedhq Organization
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import math

import appleseed as asr

from ..translator import Translator


class LampTranslator(Translator):
    def __init__(self, bl_lamp, asset_handler=None):
        super().__init__(bl_lamp, asset_handler=asset_handler)

        self.__bl_lamp_type = None

        self.__as_lamp_radiance = None
        self.__as_lamp = None

        self.__as_area_lamp_material = None
        self.__as_area_lamp_shader = None
        self.__as_area_lamp_mesh = None
        self.__as_area_lamp_mesh_inst = None

    @property
    def bl_lamp(self):
        return self._bl_obj

    def create_entities(self, bl_scene):
        as_lamp_data = self.bl_lamp.data.appleseed
        self.__bl_lamp_type = self.bl_lamp.data.type

        self.__as_lamp_model = self.__get_lamp_model()

        if self.__bl_lamp_type != 'AREA':
            if self.__as_lamp_model == 'point_light':
                as_lamp_params = self.__get_point_lamp_params()
            if self.__as_lamp_model == 'spot_light':
                as_lamp_params = self.__get_spot_lamp_params()
            if self.__as_lamp_model == 'directional_light':
                as_lamp_params = self.__get_directional_lamp_params()
            if self.__as_lamp_model == 'sun_light':
                as_lamp_params = self.__get_sun_lamp_params()

            self.__as_lamp = asr.Light(self.__as_lamp_model, self.appleseed_name, as_lamp_params)
            self.__as_lamp.set_transform(self._convert_matrix(self.bl_lamp.matrix_world))

            radiance = self._convert_color(as_lamp_data.radiance)
            lamp_radiance_name = f"{self.appleseed_name}_radiance"
            self.__as_lamp_radiance = asr.ColorEntity(lamp_radiance_name, {'color_space': 'linear_rgb'}, radiance)
        else:
            pass

    def flush_entities(self, as_assembly):
        if self.__bl_lamp_type != 'AREA':
            as_assembly.lights().insert(self.__as_lamp)
            self.__as_lamp = as_assembly.lights().get_by_name(self.appleseed_name)

            as_assembly.colors().insert(self.__as_lamp_radiance)
            self.__as_lamp_radiance = as_assembly.colors().get_by_name(f"{self.appleseed_name}_radiance")

    def set_xform_step(self, time, bl_matrix):
        pass

    def __get_point_lamp_params(self):
        as_lamp_data = self.bl_lamp.data.appleseed
        light_params = {'intensity': f"{self.appleseed_name}_radiance",
                        'intensity_multiplier': as_lamp_data.radiance_multiplier,
                        'exposure': as_lamp_data.exposure,
                        'cast_indirect_light': as_lamp_data.cast_indirect,
                        'importance_multiplier': as_lamp_data.importance_multiplier}

        return light_params

    def __get_spot_lamp_params(self):
        as_lamp_data = self.bl_lamp.data.appleseed
        outer_angle = math.degrees(self.bl_lamp.data.spot_size)
        inner_angle = (1.0 - self.bl_lamp.data.spot_blend) * outer_angle

        intensity = f"{self.appleseed_name}_radiance"
        intensity_multiplier = as_lamp_data.radiance_multiplier

        if as_lamp_data.radiance_use_tex and as_lamp_data.radiance_tex is not None:
            intensity = f"{as_lamp_data.radiance_tex.name_full}_inst"
        if as_lamp_data.radiance_multiplier_use_tex and as_lamp_data.radiance_multiplier_tex is not None:
            intensity_multiplier = f"{as_lamp_data.radiance_multiplier_tex.name_full}_inst"

        light_params = {'intensity': intensity,
                        'intensity_multiplier': intensity_multiplier,
                        'exposure': as_lamp_data.exposure,
                        'cast_indirect_light': as_lamp_data.cast_indirect,
                        'importance_multiplier': as_lamp_data.importance_multiplier,
                        'exposure_multiplier': as_lamp_data.exposure_multiplier,
                        'tilt_angle': as_lamp_data.tilt_angle,
                        'inner_angle': inner_angle,
                        'outer_angle': outer_angle}

        return light_params

    def __get_directional_lamp_params(self):
        as_lamp_data = self.bl_lamp.data.appleseed
        light_params = {'irradiance': f"{self.appleseed_name}_radiance",
                        'irradiance_multiplier': as_lamp_data.radiance_multiplier,
                        'exposure': as_lamp_data.exposure,
                        'cast_indirect_light': as_lamp_data.cast_indirect,
                        'importance_multiplier': as_lamp_data.importance_multiplier}

        return light_params

    def __get_sun_lamp_params(self):
        as_lamp_data = self.bl_lamp.data.appleseed
        light_params = {'radiance_multiplier': as_lamp_data.radiance_multiplier,
                        'cast_indirect_light': as_lamp_data.cast_indirect,
                        'importance_multiplier': as_lamp_data.importance_multiplier,
                        'size_multiplier': as_lamp_data.size_multiplier,
                        'distance': as_lamp_data.distance,
                        'turbidity': as_lamp_data.turbidity}

        if as_lamp_data.use_edf:
            light_params['environment_edf'] = 'sky_edf'

        return light_params

    def __get_lamp_model(self):
        as_lamp_data = self.bl_lamp.data.appleseed
        if self.__bl_lamp_type == 'POINT':
            return 'point_light'
        if self.__bl_lamp_type == 'SPOT':
            return 'spot_light'
        if self.__bl_lamp_type == 'SUN' and as_lamp_data.sun_mode == 'distant':
            return 'directional_light'
        if self.__bl_lamp_type == 'SUN' and as_lamp_data.sun_mode == 'sun':
            return 'sun_light'
