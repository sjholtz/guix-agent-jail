import logging
import os
from datetime import datetime as dt
from pathlib import Path
from dotenv import load_dotenv
from mitmproxy import http, ctx

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


class KeyInjector:
    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host
        logger.info(f"[KeyInjector:{now}] Intercepted request to: {host}")

        # OpenAI Header Injection
        if "api.openai.com" in host:
            key = os.getenv("HOST_OPENAI_API_KEY")
            if key:
                flow.request.headers["Authorization"] = f"Bearer {key}"
                logger.info(f"[KeyInjector:{now}] Injected HOST_OPENAI_API_KEY")
            else:
                logger.info(f"[KeyInjector:{now}] HOST_OPENAI_API_KEY is not set!")

        # Anthropic Header Injection
        elif "api.anthropic.com" in host:
            key = os.getenv("HOST_ANTHROPIC_API_KEY")
            if key:
                flow.request.headers["x-api-key"] = key
                logger.info(f"[KeyInjector:{now}] Injected HOST_ANTHROPIC_API_KEY")
            else:
                logger.info(f"[KeyInjector:{now}] HOST_ANTHROPIC_API_KEY is not set!")

        # Ollama Header Injection
        elif "ollama.com" in host:
            key = os.getenv("HOST_OLLAMA_API_KEY")
            if key:
                flow.request.headers["Authorization"] = f"Bearer {key}"
                logger.info(f"[KeyInjector:{now}] Injected HOST_OLLAMA_API_KEY")
            else:
                logger.info(f"[KeyInjector:{now}] HOST_OLLAMA_API_KEY is not set!")

        # LangSmith tracing Header Injection
        elif host == "api.smith.langchain.com":
            key = os.getenv("HOST_LANGSMITH_API_KEY")
            if key:
                flow.request.headers["x-api-key"] = key
                logger.info(f"[KeyInjector:{now}] Injected HOST_LANGSMITH_API_KEY")
            else:
                logger.info(f"[KeyInjector:{now}] HOST_LANGSMITH_API_KEY is not set!")


addons = [KeyInjector()]
