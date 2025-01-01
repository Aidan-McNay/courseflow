"""Sets common variables and drivers for the Canvas course.

Required environment variables:
 - CANVAS_API_KEY: Your API key for accessing Canvas
"""

import canvasapi
import os
from typing import cast

if "AUTODOC_GEN" in os.environ:
    _course_id = cast(int, object())
    _canvas = cast(canvasapi.Canvas, object())
    _course = cast(canvasapi.course.Course, object())
else:
    # The Canvas course ID
    _course_id = int(os.environ["CANVAS_API_COURSEID"])

    # Access to the Canvas API, to be used by the module
    _canvas = canvasapi.Canvas(
        base_url="https://canvas.cornell.edu",
        access_token=os.environ["CANVAS_API_KEY"],
    )

    # The specific course we want to have access to
    _course = _canvas.get_course(_course_id)
