---
name: Jarvis runtime
description: Runtime constraint for running the Jarvis Mark V Python service in Replit
---

The Jarvis Mark V service should run with the managed Python 3.12 runtime rather than the base Python 3.13 module.

**Why:** The base Python 3.13 environment is externally managed and does not provide pip, so dependency installation fails before the application can start.

**How to apply:** When setting up or restarting this repository in a new Replit project, select the managed `python-3.12` runtime before installing `requirements.txt` or configuring the server workflow.