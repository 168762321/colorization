from flask_restx import Namespace, fields


class ColorizeDto:
    api = Namespace("colorize", description="Colorize Video.")

    colorize_obj = api.model(
        "Colorizer object",
        {
            "project_id": fields.Integer,
            "shortcut_id": fields.Integer,
            "colorizer_id": fields.Integer,
            "output_path": fields.String,
        },
    )
