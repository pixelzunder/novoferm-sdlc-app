---
name: check-page
description: Look at the configurator page in a real browser. Use after every change of web.py, of the page texts or of anything the form shows, before you say the change is done.
---

# Check the page

The tests call `handle()` without a socket. They do not show a broken layout, a missing label
or an error in the browser console. Look at the page yourself.

## Steps

1. Start the server in the background on a free port:
   `python -m doorcfg serve --port 8081`. Port 8080 may belong to the developer.
2. Open `http://127.0.0.1:8081/` with the MCP server `chrome-devtools`.
3. Submit the form once with a door that can be built and once with one that cannot
   (width 2500, surface smooth, drive manual, option smart_control).
4. Read the browser console. An error there is a finding, even when the page looks right.
5. Open one other language, for example `/?lang=de`. Every label of the form is translated.
6. Stop the server.

## Without a browser

When `chrome-devtools` is not connected, fetch the page with
`curl "http://127.0.0.1:8081/?width=2500&height=2125&surface=smooth"` and read the HTML. Say in
your report that nobody looked at the rendered page.

## Report

What you opened, what you saw, and what you did not check.
