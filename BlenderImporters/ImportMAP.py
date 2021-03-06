"""
Functions to import MAP files into blender
"""
import os
import sys
import logging
from math import radians

import bpy # type: ignore
import mathutils # type: ignore

sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.R6MAPStructures import R6MAPLight, R6MAPLightList
from RainbowFileReaders.RSDMPLightReader import RSDMPLight, RSDMPLightFile
from RainbowFileReaders.RSEGeometryDataStructures import R6GeometryObject
from RainbowFileReaders.RSMAPStructures import RSMAPGeometryObject

from BlenderImporters import BlenderUtils
from BlenderImporters.BlenderUtils import create_objects_from_R6GeometryObject, create_objects_from_RSMAPGeometryObject

log = logging.getLogger(__name__)

def create_spotlight_from_r6_light_specification(lightSpec: R6MAPLight, name: str):
    """Create a spotlight from a rainbow six light specification"""
    #https://stackoverflow.com/a/17355744
    lamp_data = None
    lamp_data = bpy.data.lights.new(name=lightSpec.name_string.string + "_pointdata", type='POINT')
    # Create new object with our lamp datablock
    lamp_object = bpy.data.objects.new(name=name, object_data=lamp_data)
    # Link lamp object to the scene so it'll appear in this scene
    bpy.context.scene.collection.objects.link(lamp_object)
    # And finally select it make active
    lamp_object.select_set(True)
    bpy.context.view_layer.objects.active = lamp_object

    # Place lamp to a specified location
    position = lightSpec.position
    position[0] *= -1.0
    lamp_object.location = position


    #do rotation matrix work
    matRow1 = lightSpec.transformMatrix[0:3]
    matRow2 = lightSpec.transformMatrix[3:6]
    matRow3 = lightSpec.transformMatrix[6:9]
    transformMatrix = mathutils.Matrix((matRow1, matRow2, matRow3))
    lamp_object.rotation_euler = transformMatrix.to_euler()
    importedQuat = transformMatrix.to_quaternion()

    #correct the incorrect rotation due to coordinate system conversion
    coordSystemConversionQuat = mathutils.Euler((radians(-90), 0, 0)).to_quaternion()
    finalQuat = importedQuat @ coordSystemConversionQuat
    lamp_object.rotation_euler = finalQuat.to_euler()



    color = []
    for color_el in lightSpec.color:
        color.append(color_el / 255.0)
    lamp_data.color = color

    lamp_data.falloff_type = 'INVERSE_COEFFICIENTS'
    lamp_data.constant_coefficient = lightSpec.constantAttenuation
    lamp_data.linear_coefficient = lightSpec.linearAttenuation
    lamp_data.quadratic_coefficient = lightSpec.quadraticAttenuation

    #TODO: Fix these approximations
    lamp_data.energy = lightSpec.energy * 25
    lamp_data.shadow_soft_size = lightSpec.falloff
    #lamp_data.use_custom_distance = True
    #lamp_data.distance = lightSpec.energy
    lamp_data.use_shadow = False


    #lamp_data.specular_factor = lightSpec.unknown7

    return lamp_object

def import_r6_lights(lightlist: R6MAPLightList):
    """Import all lights from a rainbow six map"""
    lightGroup = bpy.data.objects.new("LightGroup", None)
    lightGroup.location = (0,0,0)
    lightGroup.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(lightGroup)
    lightGroup.rotation_euler = (radians(90),0,0)

    for idx, light in enumerate(lightlist.lights):
        name = light.name_string.string + "_idx" + str(idx)
        newLamp = create_spotlight_from_r6_light_specification(light, name)
        newLamp.parent = lightGroup

def create_spotlight_from_rs_light_specification(lightSpec: RSDMPLight, name: str):
    """Create a spotlight from a rogue spear light specification"""
    #https://stackoverflow.com/a/17355744
    lamp_data = None
    lamp_data = bpy.data.lights.new(name=lightSpec.name_string.string + "_pointdata", type='POINT')
    # Create new object with our lamp datablock
    lamp_object = bpy.data.objects.new(name=name, object_data=lamp_data)
    # Link lamp object to the scene so it'll appear in this scene
    bpy.context.scene.collection.objects.link(lamp_object)
    # And finally select it make active
    lamp_object.select_set(True)
    bpy.context.view_layer.objects.active = lamp_object

    # Place lamp to a specified location
    position = lightSpec.position
    position[0] *= -1.0
    lamp_object.location = position

    #correct the incorrect rotation due to coordinate system conversion
    # coordSystemConversionQuat = mathutils.Euler((radians(-90), 0, 0)).to_quaternion()
    # finalQuat = importedQuat @ coordSystemConversionQuat
    # lamp_object.rotation_euler = finalQuat.to_euler()

    lamp_data.color = lightSpec.diffuseColor[:3]

    lamp_data.falloff_type = 'INVERSE_COEFFICIENTS'
    lamp_data.constant_coefficient = lightSpec.constantAttenuation
    lamp_data.linear_coefficient = lightSpec.linearAttenuation
    lamp_data.quadratic_coefficient = lightSpec.quadraticAttenuation

    #TODO: Fix these approximations
    lamp_data.energy = lightSpec.energy * 25
    lamp_data.shadow_soft_size = lightSpec.falloff
    #lamp_data.use_custom_distance = True
    #lamp_data.distance = lightSpec.energy
    lamp_data.use_shadow = False


    #lamp_data.specular_factor = lightSpec.unknown7

    return lamp_object

def import_rs_lights(dmpLightFile: RSDMPLightFile):
    """Import all lights from a rogue spear DMP file"""
    lightGroup = bpy.data.objects.new("LightGroup", None)
    lightGroup.location = (0,0,0)
    lightGroup.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(lightGroup)
    lightGroup.rotation_euler = (radians(90),0,0)

    for idx, light in enumerate(dmpLightFile.lights):
        name = light.name_string.string + "_idx" + str(idx)
        newLamp = create_spotlight_from_rs_light_specification(light, name)
        newLamp.parent = lightGroup

def import_MAP_to_scene(filename: str):
    """Imports a given map to the blender scene.
    Skips files named obstacletest.map since its an invalid test file on original rainbow six installations"""
    if filename.endswith("obstacletest.map"):
        #I believe this is an early test map that was shipped by accident.
        # It's data structures are not consistent with the rest of the map files
        # and it is not used anywhere so it is safe to skip
        log.info("Skipping test map: %s", filename)
        return False
    MAPObject = MAPLevelReader.MAPLevelFile()
    MAPObject.read_file(filename)

    BlenderUtils.setup_blank_scene()

    log.info("Beginning import")

    texturePaths = R6Settings.get_relevant_global_texture_paths(filename)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(MAPObject.materials, texturePaths)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        for geoObj in MAPObject.geometryObjects:
            if isinstance(geoObj, R6GeometryObject):
                create_objects_from_R6GeometryObject(geoObj, blenderMaterials)
    else:
        for geoObj in MAPObject.geometryObjects:
            if isinstance(geoObj, RSMAPGeometryObject):
                create_objects_from_RSMAPGeometryObject(geoObj, blenderMaterials)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        import_r6_lights(MAPObject.lightList)
    else:
        import_rs_lights(MAPObject.dmpLights)

    log.info("Import Map Succeeded")
    return True


def save_blend_scene(path: str):
    """Saves the scene to a .blend file"""
    bpy.ops.wm.save_as_mainfile(filepath=path)

def export_fbx_scene(path: str):
    """exports the scene to a .fbx file"""
    bpy.ops.export_scene.fbx(filepath=path, path_mode='RELATIVE')

def import_map_and_save(path: str):
    """Wrapper method to import a map to scene, save and export"""
    inPath = os.path.abspath(path)
    importSuccess = import_MAP_to_scene(inPath)
    if importSuccess:
        outBlendPath = inPath + ".blend"
        save_blend_scene(outBlendPath)
        outFBXPath = inPath + ".FBX"
        export_fbx_scene(outFBXPath)


if __name__ == "__main__":
    import_MAP_to_scene(sys.argv[-1])
