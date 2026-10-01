import logging
import os
import tomllib
from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from dotenv import load_dotenv
from mitmproxy import http

wd_path = Path.cwd().parent
now = dt.now().isoformat(sep=" ", timespec="seconds")

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=wd_path / "inject_keys.log",
    encoding="utf-8",
    level=logging.INFO,
)

logger.info(f"[KeyInjector:{now}] WD is {wd_path}")

env_path = wd_path / ".env.guix-agent-jail"
if not env_path.exists():
    logger.critical(f"[KeyInjector:{now}] No .env.guix-agent-jail exists in WD.")
    import sys

    sys.exit(1)
logger.info(f"[KeyInjector:{now}] Loading {env_path}")
load_dotenv(dotenv_path=env_path)


@dataclass(frozen=True)
class HeaderMapping:
    host: str
    environment_variable: str


def load_header_mappings(
    config_path: Path,
) -> dict[str, list[HeaderMapping]]:
    try:
        with config_path.open("rb") as config_file:
            configuration = tomllib.load(config_file)
    except FileNotFoundError:
        logger.critical(
            f"[KeyInjector:{now}] Header configuration not found: " f"{config_path}"
        )
        raise
    except OSError as error:
        logger.critical(
            f"[KeyInjector:{now}] Could not read header configuration "
            f"{config_path}: {error}"
        )
        raise
    except tomllib.TOMLDecodeError as error:
        logger.critical(
            f"[KeyInjector:{now}] Invalid TOML configuration " f"{config_path}: {error}"
        )
        raise

    mappings: dict[str, list[HeaderMapping]] = {}

    for section_name in ("auth", "x-api"):
        section = configuration.get(section_name, {})
        entries = section.get("headers", [])

        if not isinstance(entries, list):
            raise ValueError(f"'{section_name}.headers' must be an array of tables")

        mappings[section_name] = []

        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Entries in '{section_name}.headers' must be tables")

            host = entry.get("host")
            environment_variable = entry.get("environment_variable")

            if not isinstance(host, str) or not host:
                raise ValueError(f"Entries in '{section_name}.headers' require a host")
            if not isinstance(environment_variable, str) or not environment_variable:
                raise ValueError(
                    f"Entries in '{section_name}.headers' require an "
                    "environment_variable"
                )

            mappings[section_name].append(
                HeaderMapping(
                    host=host,
                    environment_variable=environment_variable,
                )
            )

    return mappings


class KeyInjector:
    def __init__(self) -> None:
        configured_path = os.getenv("KEY_INJECTOR_CONFIG")
        self.config_path = Path(
            configured_path
            if configured_path
            else Path.home() / ".config" / "guix-agent" / "key-injector.toml"
        )
        self.mappings = load_header_mappings(self.config_path)

    def _find_mapping(
        self,
        host: str,
        mappings: list[HeaderMapping],
    ) -> HeaderMapping | None:
        for mapping in mappings:
            if host == mapping.host or host.endswith(f".{mapping.host}"):
                return mapping

        logger.debug(f"[KeyInjector:{now}] No header mapping matched host: {host}")
        return None

    def _inject_header(
        self,
        flow: http.HTTPFlow,
        header_name: str,
        mappings: list[HeaderMapping],
    ) -> None:
        host = flow.request.pretty_host
        mapping = self._find_mapping(host, mappings)

        if not mapping:
            return

        key = os.getenv(mapping.environment_variable)

        if not key:
            logger.warning(
                f"[KeyInjector:{now}] {mapping.environment_variable} is not "
                f"set; could not inject {header_name} for {host}"
            )
            return

        prefix = "Bearer " if header_name == "Authorization" else ""
        flow.request.headers[header_name] = f"{prefix}{key}"
        logger.info(
            f"[KeyInjector:{now}] Injected {mapping.environment_variable} "
            f"into {header_name}"
        )

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host
        logger.info(f"[KeyInjector:{now}] Intercepted request to: {host}")

        self._inject_header(
            flow,
            "Authorization",
            self.mappings["auth"],
        )

        self._inject_header(
            flow,
            "x-api-key",
            self.mappings["x-api"],
        )


addons = [KeyInjector()]
