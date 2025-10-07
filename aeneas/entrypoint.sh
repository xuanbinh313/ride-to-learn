#!/bin/bash
# A simple entrypoint to run aeneas commands in container

# If first arg is something like “python3 -m aeneas.tools…” then just exec
if [[ "$1" == "python3" ]]; then
  exec "$@"
fi

# Otherwise, we assume user wants to run `execute_task` or `execute_job`
# Example: container audio.mp3 text.txt "task_language=eng|..." output.json
exec python3 -m aeneas.tools.execute_task "$@"
