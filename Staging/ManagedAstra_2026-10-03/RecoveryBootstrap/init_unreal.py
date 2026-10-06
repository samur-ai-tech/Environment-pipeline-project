"""Process-scoped recovery entrypoint; only selected via reviewed launch env."""
import os
if os.environ.get('GEOCITY_RECOVERY_STARTUP_TOKEN') == 'ROOT_ACTIVATED_REPLACEMENT_EDITOR_STARTUP':
    import recovery_startup
    recovery_startup.start()
