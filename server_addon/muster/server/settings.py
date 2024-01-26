from ayon_server.settings import BaseSettingsModel, SettingsField


class TemplatesMapping(BaseSettingsModel):
    _layout = "compact"
    name: str = SettingsField(title="Name")
    value: int = SettingsField(title="mapping")


class MusterSettings(BaseSettingsModel):
    enabled: bool = True
    MUSTER_REST_URL: str = SettingsField(
        "",
        title="Muster Rest URL",
        scope=["studio"],
    )

    templates_mapping: list[TemplatesMapping] = SettingsField(
        default_factory=list,
        title="Templates mapping",
    )


DEFAULT_VALUES = {
    "enabled": False,
    "MUSTER_REST_URL": "http://127.0.0.1:9890",
    "templates_mapping": [
        {"name": "file_layers", "value": 7},
        {"name": "mentalray", "value": 2},
        {"name": "mentalray_sf", "value": 6},
        {"name": "redshift", "value": 55},
        {"name": "renderman", "value": 29},
        {"name": "software", "value": 1},
        {"name": "software_sf", "value": 5},
        {"name": "turtle", "value": 10},
        {"name": "vector", "value": 4},
        {"name": "vray", "value": 37},
        {"name": "ffmpeg", "value": 48}
    ]
}
