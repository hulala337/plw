"""Windows desktop entry point. Implementation lives in workbench/."""
from workbench import routes  # Registers HTTP routes once.
from workbench.runtime import api
from workbench.application import main, shutdown_runtime

if __name__ == "__main__":
    try:
        main()
    finally:
        shutdown_runtime()
