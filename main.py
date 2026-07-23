"""Graphical entry point for YOLO Utilities."""

import sys

from yolo_utils.gui import Application, run


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        application = Application()
        application.withdraw()
        application.update_idletasks()
        application.destroy()
    else:
        run()
