---
name: Preview cache behavior
description: The Replit preview can display an older HTML response even after the workflow restarts.
---

The app preview may retain a stale document for the root path while direct HTTP requests already return the current HTML. A cache-busting query string makes the current interface visible.

**Why:** The Jarvis preview continued showing the former minimal page even after the server served the rewritten HUD HTML and sent no-cache headers.

**How to apply:** When the preview and `curl` disagree, verify the served HTML directly and reload the preview with a query string such as `/?refresh=<version>` before changing application code.