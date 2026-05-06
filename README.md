# envoy-local

Lightweight wrapper to manage `.env` files across multiple projects with secret masking.

---

## Installation

```bash
pip install envoy-local
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envoy-local
```

---

## Usage

```python
from envoy_local import EnvoyLocal

# Load and manage a .env file with secrets masked in output
env = EnvoyLocal(".env")

# List all variables (secrets are masked)
env.list()
# DB_HOST     = localhost
# DB_PASSWORD = ********
# API_KEY     = ********

# Get a raw value
db_host = env.get("DB_HOST")

# Set a new variable
env.set("NEW_VAR", "my_value")

# Switch to a different project's .env file
env.load("/path/to/other/project/.env")
```

### CLI

```bash
# List variables in a .env file
envoy list --file /path/to/project/.env

# Add or update a variable
envoy set MY_SECRET supersecretvalue --file .env

# Remove a variable
envoy unset MY_SECRET --file .env
```

---

## Features

- 🔒 Automatic secret masking for sensitive keys (`PASSWORD`, `SECRET`, `KEY`, `TOKEN`)
- 📁 Manage `.env` files across multiple projects from one place
- 🖥️ Simple CLI and Python API
- ⚡ Zero heavy dependencies

---

## License

MIT © [envoy-local contributors](https://github.com/your-username/envoy-local)