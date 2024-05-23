# -*- coding: utf-8 -*-
"""Creator plugin for creating textures."""
from ayon_core.pipeline import CreatedInstance, Creator, CreatorError
from ayon_core.lib import (
    EnumDef,
    UILabelDef,
    NumberDef,
    BoolDef
)

from ayon_core.hosts.substancepainter.api.pipeline import (
    get_instances,
    set_instance,
    set_instances,
    remove_instance
)
from ayon_core.hosts.substancepainter.api.lib import get_export_presets

import substance_painter
import substance_painter.project


class CreateTextures(Creator):
    """Create a texture set."""
    identifier = "io.openpype.creators.substancepainter.textureset"
    label = "Textures"
    product_type = "textureSet"
    icon = "picture-o"

    default_variant = "Main"
    channel_mapping = []

    def apply_settings(self, project_settings):
        settings = project_settings["substancepainter"].get("create", [])  # noqa
        if settings:
            self.channel_mapping = settings["CreateTextures"].get(
                "channel_mapping", [])


    def create(self, product_name, instance_data, pre_create_data):
        if not substance_painter.project.is_open():
            raise CreatorError("Can't create a Texture Set instance without "
                               "an open project.")
        # Transfer settings from pre create to instance
        creator_attributes = instance_data.setdefault(
            "creator_attributes", dict())
        for key in [
            "exportPresetUrl",
            "exportFileFormat",
            "exportSize",
            "exportPadding",
            "exportDilationDistance",
            "useCustomExportPreset",
            "exportChannel"
        ]:
            if key in pre_create_data:
                creator_attributes[key] = pre_create_data[key]

        if pre_create_data.get("use_selection"):
            stack = substance_painter.textureset.get_active_stack()

            instance_data["selected_node_id"] = [
                node_number.uid() for node_number in
                substance_painter.layerstack.get_selected_nodes(stack)]

        instance = self.create_instance_in_context(product_name,
                                                   instance_data)
        set_instance(
            instance_id=instance["instance_id"],
            instance_data=instance.data_to_store()
        )

    def collect_instances(self):
        for instance in get_instances():
            if (instance.get("creator_identifier") == self.identifier or
                    instance.get("productType") == self.product_type):
                self.create_instance_in_context_from_existing(instance)

    def update_instances(self, update_list):
        instance_data_by_id = {}
        for instance, _changes in update_list:
            # Persist the data
            instance_id = instance.get("instance_id")
            instance_data = instance.data_to_store()
            instance_data_by_id[instance_id] = instance_data
        set_instances(instance_data_by_id, update=True)

    def remove_instances(self, instances):
        for instance in instances:
            remove_instance(instance["instance_id"])
            self._remove_instance_from_context(instance)

    # Helper methods (this might get moved into Creator class)
    def create_instance_in_context(self, product_name, data):
        instance = CreatedInstance(
            self.product_type, product_name, data, self
        )
        self.create_context.creator_adds_instance(instance)
        return instance

    def create_instance_in_context_from_existing(self, data):
        instance = CreatedInstance.from_existing(data, self)
        self.create_context.creator_adds_instance(instance)
        return instance

    def get_instance_attr_defs(self):
        export_channel_enum = {
            item["value"]: item["name"]
            for item in self.channel_mapping
        }

        return [
            EnumDef("exportChannel",
                    items=export_channel_enum,
                    multiselection=True,
                    default=None,
                    label="Export Channel(s)",
                    tooltip="Choose the channel which you "
                            "want to solely export. The value "
                            "is 'None' by default which exports "
                            "all channels"),
            EnumDef("exportPresetUrl",
                    items=get_export_presets(),
                    label="Output Template"),
            BoolDef("allowSkippedMaps",
                    label="Allow Skipped Output Maps",
                    tooltip="When enabled this allows the publish to ignore "
                            "output maps in the used output template if one "
                            "or more maps are skipped due to the required "
                            "channels not being present in the current file.",
                    default=True),
            EnumDef("exportFileFormat",
                    items={
                        None: "Based on output template",
                        # TODO: Get available extensions from substance API
                        "bmp": "bmp",
                        "ico": "ico",
                        "jpeg": "jpeg",
                        "jng": "jng",
                        "pbm": "pbm",
                        "pgm": "pgm",
                        "png": "png",
                        "ppm": "ppm",
                        "tga": "targa",
                        "tif": "tiff",
                        "wap": "wap",
                        "wbmp": "wbmp",
                        "xpm": "xpm",
                        "gif": "gif",
                        "hdr": "hdr",
                        "exr": "exr",
                        "j2k": "j2k",
                        "jp2": "jp2",
                        "pfm": "pfm",
                        "webp": "webp",
                        # TODO: Unsure why jxr format fails to export
                        # "jxr": "jpeg-xr",
                        # TODO: File formats that combine the exported textures
                        #   like psd are not correctly supported due to
                        #   publishing only a single file
                        # "psd": "psd",
                        # "sbsar": "sbsar",
                    },
                    default=None,
                    label="File type"),
            EnumDef("exportSize",
                    items={
                        None: "Based on each Texture Set's size",
                        #  The key is size of the texture file in log2.
                        #  (i.e. 10 means 2^10 = 1024)
                        7: "128",
                        8: "256",
                        9: "512",
                        10: "1024",
                        11: "2048",
                        12: "4096",
                        13: "8192"
                    },
                    default=None,
                    label="Size"),
            EnumDef("exportPadding",
                    items={
                        "passthrough": "No padding (passthrough)",
                        "infinite": "Dilation infinite",
                        "transparent": "Dilation + transparent",
                        "color": "Dilation + default background color",
                        "diffusion": "Dilation + diffusion"
                    },
                    default="infinite",
                    label="Padding"),
            NumberDef("exportDilationDistance",
                      minimum=0,
                      maximum=256,
                      decimals=0,
                      default=16,
                      label="Dilation Distance"),
            UILabelDef("*only used with "
                       "'Dilation + <x>' padding"),
        ]

    def get_pre_create_attr_defs(self):
        # Use same attributes as for instance attributes
        selection_list = []
        if  substance_painter.application.version_info()[0] >= 10:
            selection_list = [
                BoolDef("use_selection", label="Use selection",
                        tooltip="Select Layer Stack(s) for exporting")
            ]
        return selection_list + self.get_instance_attr_defs()
