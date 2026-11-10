"""Flask front end for the BJT common-emitter DC bias calculator."""

from flask import Flask, render_template, request

from bjt_bias.engineering import analyze
from bjt_bias.validation import parse_inputs


def create_app() -> Flask:
    """Build the Flask application."""
    app = Flask(__name__)

    @app.template_filter("ma")
    def milliamps(amps: float) -> str:
        return f"{amps * 1000.0:.3f}"

    @app.template_filter("v")
    def volts(value: float) -> str:
        return f"{value:.3f}"

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            return render_template(
                "index.html", raw={}, errors={}, warnings=[], result=None
            )

        parsed = parse_inputs(request.form)
        result = analyze(parsed.inputs) if parsed.inputs is not None else None
        return render_template(
            "index.html",
            raw=parsed.raw,
            errors=parsed.errors,
            warnings=parsed.warnings,
            result=result,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
