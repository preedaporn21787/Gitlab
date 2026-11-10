"""Flask front end for the BJT common-emitter DC bias calculator."""

from flask import Flask, render_template, request

from bjt_bias.engineering import analyze
from bjt_bias.plotting import circuit_svg, load_line_svg
from bjt_bias.validation import parse_inputs


def create_app() -> Flask:
    """Build the Flask application."""
    app = Flask(__name__)

    @app.template_filter("ma")
    def milliamps(amps: float) -> str:
        return f"{amps * 1000.0:.2f}"

    @app.template_filter("ua")
    def microamps(amps: float) -> str:
        return f"{amps * 1_000_000.0:.1f}"

    @app.template_filter("v")
    def volts(value: float) -> str:
        return f"{value:.2f}"

    def _display_labels(raw: dict[str, str], units: dict[str, str]) -> dict[str, str]:
        """รวมค่าที่พิมพ์กับหน่วยเป็นข้อความสำหรับแผนภาพวงจร."""
        labels: dict[str, str] = {}
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            value = raw.get(field, "")
            unit = units.get(field, "")
            if value:
                labels[field] = f"{value} {unit}".strip() if unit else value
        return labels

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            return render_template(
                "index.html",
                raw={},
                units={},
                errors={},
                warnings=[],
                result=None,
                circuit_svg=circuit_svg({}),
                chart_svg=None,
            )

        parsed = parse_inputs(request.form)
        result = analyze(parsed.inputs) if parsed.inputs is not None else None
        chart_svg = (
            load_line_svg(parsed.inputs, result.primary) if result is not None else None
        )
        return render_template(
            "index.html",
            raw=parsed.raw,
            units=parsed.units,
            errors=parsed.errors,
            warnings=parsed.warnings,
            result=result,
            circuit_svg=circuit_svg(_display_labels(parsed.raw, parsed.units)),
            chart_svg=chart_svg,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
