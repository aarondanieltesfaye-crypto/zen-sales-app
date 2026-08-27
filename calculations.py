def calculate_zen_revenue(gross_sale, quantity, commission_type, commission_value):
    try:
        val = float(commission_value)
        if commission_type == "Percentage":
            return gross_sale * (val / 100.0)
        elif commission_type == "Fixed":
            return quantity * val
        return 0.0
    except:
        return 0.0