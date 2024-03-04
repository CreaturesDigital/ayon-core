import collections

import ayon_api
import pyblish.api

from ayon_core.client import (
    get_subsets,
    get_last_versions,
    get_representations,
)
from ayon_core.pipeline.load import get_representation_path_with_anatomy


class CollectAudio(pyblish.api.ContextPlugin):
    """Collect folders's last published audio.

    The audio product name searched for is defined in:
        project settings > Collect Audio

    Note:
        The plugin was instance plugin but because of so much queries the
            plugin was slowing down whole collection phase a lot thus was
            converted to context plugin which requires only 4 queries top.
    """

    label = "Collect Folder Audio"
    order = pyblish.api.CollectorOrder + 0.1
    families = ["review"]
    hosts = [
        "nuke",
        "maya",
        "shell",
        "hiero",
        "premiere",
        "harmony",
        "traypublisher",
        "fusion",
        "tvpaint",
        "resolve",
        "webpublisher",
        "aftereffects",
        "flame",
        "unreal"
    ]

    audio_product_name = "audioMain"

    def process(self, context):
        # Fake filtering by family inside context plugin
        filtered_instances = []
        for instance in pyblish.api.instances_by_plugin(
            context, self.__class__
        ):
            # Skip instances that already have audio filled
            if instance.data.get("audio"):
                self.log.debug(
                    "Skipping Audio collection. It is already collected"
                )
                continue
            filtered_instances.append(instance)

        # Skip if none of instances remained
        if not filtered_instances:
            return

        # Add audio to instance if exists.
        instances_by_folder_path = collections.defaultdict(list)
        for instance in filtered_instances:
            folder_path = instance.data["folderPath"]
            instances_by_folder_path[folder_path].append(instance)

        folder_paths = set(instances_by_folder_path.keys())
        self.log.debug((
            "Searching for audio product '{product}' in folders {folders}"
        ).format(
            product=self.audio_product_name,
            folders=", ".join([
                '"{}"'.format(folder_path)
                for folder_path in folder_paths
            ])
        ))

        # Query all required documents
        project_name = context.data["projectName"]
        anatomy = context.data["anatomy"]
        repre_docs_by_folder_paths = self.query_representations(
            project_name, folder_paths)

        for folder_path, instances in instances_by_folder_path.items():
            repre_docs = repre_docs_by_folder_paths[folder_path]
            if not repre_docs:
                continue

            repre_doc = repre_docs[0]
            repre_path = get_representation_path_with_anatomy(
                repre_doc, anatomy
            )
            for instance in instances:
                instance.data["audio"] = [{
                    "offset": 0,
                    "filename": repre_path
                }]
                self.log.debug("Audio Data added to instance ...")

    def query_representations(self, project_name, folder_paths):
        """Query representations related to audio products for passed folders.

        Args:
            project_name (str): Project in which we're looking for all
                entities.
            folder_paths (Iterable[str]): Folder paths where to look for audio
                products and their representations.

        Returns:
            collections.defaultdict[str, List[Dict[Str, Any]]]: Representations
                related to audio products by folder path.
        """

        output = collections.defaultdict(list)
        # Query folder entities
        folder_entities = ayon_api.get_folders(
            project_name,
            folder_paths=folder_paths,
            fields={"id", "path"}
        )

        folder_id_by_path = {
            folder_entity["path"]: folder_entity["id"]
            for folder_entity in folder_entities
        }
        folder_ids = set(folder_id_by_path.values())

        # Query products with name define by 'audio_product_name' attr
        # - one or none products with the name should be available on
        #   an folder
        subset_docs = get_subsets(
            project_name,
            subset_names=[self.audio_product_name],
            asset_ids=folder_ids,
            fields=["_id", "parent"]
        )
        product_id_by_folder_id = {}
        for subset_doc in subset_docs:
            folder_id = subset_doc["parent"]
            product_id_by_folder_id[folder_id] = subset_doc["_id"]

        product_ids = set(product_id_by_folder_id.values())
        if not product_ids:
            return output

        # Find all latest versions for the products
        version_docs_by_product_id = get_last_versions(
            project_name, subset_ids=product_ids, fields=["_id", "parent"]
        )
        version_id_by_product_id = {
            product_id: version_doc["_id"]
            for product_id, version_doc in version_docs_by_product_id.items()
        }
        version_ids = set(version_id_by_product_id.values())
        if not version_ids:
            return output

        # Find representations under latest versions of audio products
        repre_docs = get_representations(
            project_name, version_ids=version_ids
        )
        repre_docs_by_version_id = collections.defaultdict(list)
        for repre_doc in repre_docs:
            version_id = repre_doc["parent"]
            repre_docs_by_version_id[version_id].append(repre_doc)

        if not repre_docs_by_version_id:
            return output

        for folder_path in folder_paths:
            folder_id = folder_id_by_path.get(folder_path)
            product_id = product_id_by_folder_id.get(folder_id)
            version_id = version_id_by_product_id.get(product_id)
            output[folder_path] = repre_docs_by_version_id[version_id]
        return output
