"""Flask front end for the BJT DC bias calculator and CE amplifier simulator."""

from datetime import datetime, timezone

from flask import Flask, render_template, request

from bjt_bias.engineering import analyze
from bjt_bias.plotting import ce_circuit_svg, circuit_svg, load_line_svg
from bjt_bias.spice_engine import MODEL_NAME, run_simulation
from bjt_bias.spice_plots import ac_svg, transient_svg
from bjt_bias.spice_validation import DEFAULTS, parse_spice_inputs
from bjt_bias.validation import BIAS_TYPE_LABELS, parse_inputs


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
                bias_type="voltage_divider",
                bias_type_labels=BIAS_TYPE_LABELS,
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
            circuit_svg=circuit_svg(
                _display_labels(parsed.raw, parsed.units), parsed.bias_type
            ),
            chart_svg=chart_svg,
            bias_type=parsed.bias_type,
            bias_type_labels=BIAS_TYPE_LABELS,
        )

    @app.route("/simulate", methods=["GET", "POST"])
    def simulate():
        if request.method == "GET":
            return render_template(
                "simulator.html",
                raw=DEFAULTS, units={}, errors={}, analysis="dc",
                defaults=DEFAULTS, sim_result=None, status="idle",
                ac_plot="", tran_plot="", run_at=None, model=MODEL_NAME,
                circuit_svg=ce_circuit_svg(),
            )

        parsed = parse_spice_inputs(request.form)
        analysis = parsed.raw.get("analysis", "dc")
        if parsed.inputs is None:
            return render_template(
                "simulator.html",
                raw=parsed.raw, units=parsed.units, errors=parsed.errors,
                analysis=analysis, defaults=DEFAULTS, sim_result=None,
                status="invalid", ac_plot="", tran_plot="", run_at=None,
                model=MODEL_NAME, circuit_svg=ce_circuit_svg(),
            )

        sim_result = run_simulation(parsed.inputs)
        ac_plot = ac_svg(sim_result.ac) if sim_result.ac else ""
        tran_plot = transient_svg(sim_result.transient) if sim_result.transient else ""
        return render_template(
            "simulator.html",
            raw=parsed.raw, units=parsed.units, errors=parsed.errors,
            analysis=analysis, defaults=DEFAULTS, sim_result=sim_result,
            status=sim_result.status, ac_plot=ac_plot, tran_plot=tran_plot,
            run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model=MODEL_NAME, circuit_svg=ce_circuit_svg(),
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
