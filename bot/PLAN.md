# Bot Development Plan

This bot is designed with a clear separation between business logic and transport layers. The handlers are pure Python functions that accept a string input and return a string output. This makes them testable without Telegram and enables a CLI-based test mode.

The entry point (bot.py) is responsible for parsing input, routing commands, and optionally integrating with Telegram in later stages. In test mode, the bot bypasses Telegram entirely and directly invokes handler functions.

The handlers directory contains command-specific logic such as /start, /help, /health, and others. These handlers may call services such as an LMS API client or an LLM client, which are placed in the services directory.

Configuration is managed via environment variables loaded from .env.bot.secret using config.py. This ensures flexibility across environments.

Future tasks will extend handlers with real API calls, add intent recognition for natural language queries, and integrate Telegram polling. Deployment will be handled via a persistent background process on the VM.
