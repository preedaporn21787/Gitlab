def analyze_dc(voltage_v: float, resistance_ohm: float) -> dict[str, float]:
    """Calculate current and power for a DC voltage across a resistance."""
    if resistance_ohm <= 0:
        raise ValueError("resistance_ohm must be greater than zero")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


if __name__ == "__main__":
    try:
        voltage_v = float(input("กรอกแรงดันไฟฟ้า (โวลต์): "))
        resistance_ohm = float(input("กรอกความต้านทาน (โอห์ม): "))
        result = analyze_dc(voltage_v, resistance_ohm)
    except ValueError as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
    else:
        print(f"กระแสไฟฟ้า: {result['current_a']} แอมแปร์")
        print(f"กำลังไฟฟ้า: {result['power_w']} วัตต์")