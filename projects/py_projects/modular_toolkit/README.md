## Installation Notes (Debian/Kali)

Kali Linux enforces PEP 668, which prevents installing Python packages
system-wide using pip.

For this reason, a Python virtual environment is used to install
non-repository dependencies such as `mss`.

Before running the tool:

```bash
source venv/bin/activate