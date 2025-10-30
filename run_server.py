#!/usr/bin/env python3
"""Main entry point for running the Hephaestus MCP server."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.core.simple_config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hephaestus_server.log"),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Run the MCP server."""
    config = get_config()

    logger.info("Starting Hephaestus MCP Server")
    logger.info(f"Server will run on {config.mcp_host}:{config.mcp_port}")
    logger.info(f"Using LLM provider: {config.llm_provider}")
    logger.info(f"Using model: {config.llm_model}")

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Run the server
    try:
        uvicorn.run(
            "src.mcp.server:app",
            host=config.mcp_host,
            port=config.mcp_port,
            reload=config.debug,
            log_level="info" if not config.debug else "debug",
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()