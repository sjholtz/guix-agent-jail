import logging
import os
from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path

import tomllib
from dotenv import load_dotenv
from mitmproxy import http

wd_path = Path.cwd().parent

logger = logging.getLogger(__name__)
log_path = (
    Path(os.getenv("KEY_INJECTOR_LOG", str(wd_path / "inject_keys.log")))
    .expanduser()
    .resolve()
)
logger.setLevel(logging.INFO)

# mitmdump may configure the root logger before loading this addon, in which
# case logging.basicConfig() does nothing. Attach a file handler directly to
# this logger without replacing mitmdump's own handlers.
if not any(
    isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path
    for handler in logger.handlers
):
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [KeyInjector]: %(message)s"
        )
    )
    logger.addHandler(file_handler)


logger.info(f"WD is {wd_path}")

env_path = wd_path / ".env.guix-agent-jail"
if not env_path.exists():
    logger.critical("No .env.guix-agent-jail exists in WD.")
    import sys

    sys.exit(1)
logger.info(f"Loading {env_path}")
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
        logger.critical(f"Header configuration not found: {config_path}")
        raise
    except OSError as error:
        logger.critical(f"Could not read header configuration {config_path}: {error}")
        raise
    except tomllib.TOMLDecodeError as error:
        logger.critical(f"Invalid TOML configuration {config_path}: {error}")
        raise

    mappings: dict[str, list[HeaderMapping]] = {}

    for section_name in ("auth", "x-api"):
        section = configuration.get(section_name, {})
        entries = section.get("headers", [])

        if not isinstance(entries, list):
            raise TypeError(f"'{section_name}.headers' must be an array of tables")

        mappings[section_name] = []

        for entry in entries:
            if not isinstance(entry, dict):
                raise TypeError(f"Entries in '{section_name}.headers' must be tables")

            host = entry.get("host")
            environment_variable = entry.get("environment_variable")

            if not isinstance(host, str) or not host:
                raise TypeError(f"Entries in '{section_name}.headers' require a host")
            if not isinstance(environment_variable, str) or not environment_variable:
                raise TypeError(
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

        logger.debug(f"No header mapping matched host: {host}")
        return None

    def _inject_header(
        self,
        flow: http.HTTPFlow,
        host: str,
        header_name: str,
        mappings: list[HeaderMapping],
    ) -> None:
        mapping = self._find_mapping(host, mappings)

        if not mapping:
            return

        key = os.getenv(mapping.environment_variable)

        if not key:
            logger.warning(
                f"{mapping.environment_variable} is not set; could not "
                f"inject {header_name} for {host}"
            )
            return

        prefix = "Bearer " if header_name == "Authorization" else ""
        flow.request.headers[header_name] = f"{prefix}{key}"
        logger.info(f"Injected {mapping.environment_variable} into {header_name}")

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host
        logger.info(f"Intercepted request to: {host}")

        self._inject_header(
            flow,
            host,
            "Authorization",
            self.mappings["auth"],
        )

        self._inject_header(
            flow,
            host,
            "x-api-key",
            self.mappings["x-api"],
        )


addons = [KeyInjector()]
