import yaml

from logforge.core.config import ConfigManager, default_config_dict


def test_default_config_loads(tmp_path):
    config_path = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_path)
    config = manager.load()

    assert config.api.port == 8080
    assert config.logging.level == "INFO"


def test_env_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_path)
    monkeypatch.setenv("LOGFORGE_API_PORT", "9001")
    config = manager.load()
    assert config.api.port == 9001


def test_save_default_writes_file(tmp_path):
    config_path = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_path)
    manager.save_default()

    assert config_path.exists()
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert data == default_config_dict()
