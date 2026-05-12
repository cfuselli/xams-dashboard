import configparser
from dataclasses import dataclass
import os


def _load_xams_config() -> dict[str, str]:
    path = os.getenv("XAMS_CONFIG_FILE", os.path.join(os.path.expanduser("~"), ".xams_config"))
    if not os.path.exists(path):
        return {}
    cp = configparser.ConfigParser()
    cp.read(path)
    if "default" not in cp:
        return {}
    return {k.upper(): v for k, v in cp["default"].items()}


_XAMS = _load_xams_config()


def _cfg_env(name: str, fallback: str) -> str:
    return os.getenv(name, _XAMS.get(name, fallback))


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = _cfg_env(
        "XAMS_MONGO_URI",
        f"mongodb://{_XAMS.get('MONGO_USER', 'user')}:{_XAMS.get('MONGO_PASSWORD', 'password')}@127.0.0.1:{_XAMS.get('MONGO_PORT', '27017')}/admin",
    )
    run_db: str = os.getenv("XAMS_RUN_DB", "run")
    run_collection: str = os.getenv("XAMS_RUN_COLLECTION", "runs_gas")
    processing_db: str = os.getenv("XAMS_PROCESSING_DB", "daq")
    processing_collection: str = os.getenv("XAMS_PROCESSING_COLLECTION", "processing")

    stbc_amstrax_dir: str = _cfg_env(
        "XAMS_STBC_AMSTRAX_DIR", "/data/xenon/xams_v2/software/amstrax/amstrax/auto_processing_new"
    )
    stbc_log_dir: str = _cfg_env("XAMS_STBC_LOG_DIR", "/data/xenon/xams_v2/logs")
    stbc_output_dir: str = _cfg_env("XAMS_STBC_OUTPUT_DIR", _XAMS.get("XAMS_PROCESSED_FOLDER", "/data/xenon/xams_v2/xams_processed"))


settings = Settings()
