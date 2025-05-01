import os
import ezdxf
import math


#This program calculates Weight, Total Tool Path length, width, length, added densities table and give number of files in the folder version 2.0 built with ChatGpt Dated April 29, 2025 10:21AM Karachi time

# -----------------
# Problem
# the program is printing width and length table twice, other than that program is running fine
# ------------------

# Metal price per ton based on weight ranges (converted to €/kg)
price_per_kg_by_weight = {
    5: 3360 / 1000,
    10: 2112 / 1000,
    20: 1920 / 1000,
    50: 1632 / 1000,
    100: 1469 / 1000,
    300: 1363 / 1000,
    500: 1248 / 1000,
    1000: 1200 / 1000,
    2000: 1180 / 1000,
    3000: 1152 / 1000,
    4000: 1104 / 1000,
    5000: 1075 / 1000,
    7000: 1046 / 1000,
    10000: 1013 / 1000,
}

# Cutting time pricing in EUR based on duration in minutes (per thickness mm)
cutting_price_by_thickness_and_time = {
    0.5: [160, 120, 100, 90, 85, 80, 75, 73, 70],
    1:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    2:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    3:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    4:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    5:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    6:   [160, 120, 100, 90, 85, 80, 75, 73, 70],
    8:   [170, 130, 110, 100, 95, 90, 85, 83, 80],
    10:  [170, 130, 110, 100, 95, 90, 85, 83, 80],
    12:  [170, 130, 110, 100, 95, 90, 85, 83, 80],
    15:  [180, 140, 120, 110, 105, 100, 95, 93, 90],
    16:  [180, 140, 120, 110, 105, 100, 95, 93, 90],
    20:  [180, 140, 120, 110, 105, 100, 95, 93, 90],
    25:  [190, 150, 130, 120, 115, 110, 105, 103, 100],
    30:  [200, 160, 140, 130, 125, 120, 115, 113, 110],
    40:  [210, 170, 150, 140, 135, 130, 125, 123, 120],
    50:  [220, 180, 160, 150, 145, 140, 135, 133, 130],
}

# ----------------------------
# DENSITY TABLE (kg/m³)
# ----------------------------
DENSITIES = {
    "aluminium": 2700,
    "steel": 7850,
    "stainless_steel": 8100,
    "titanium": 4500,
    "brass": 7500,
}

# ----------------------------
# UNIT CONVERSION (DXF INSUNITS to meters)
# ----------------------------
INSUNITS_TO_METERS = {
    0: 1.0,
    1: 0.0254,
    2: 0.3048,
    3: 1609.344,
    4: 0.001,
    5: 0.01,
    6: 1.0,
    7: 1000.0,
    8: 2.54e-5,
    9: 0.000254,
}

# ----------------------------
# CUTTING SPEED & PIERCING DELAY by THICKNESS (from PDF)
# ----------------------------
THICKNESS_PROPERTIES = {
    "1-3mm": {"min": 1, "max": 3, "speed_m_per_min": 8.0,   "piercing_delay_s": 0.5},
    "4-6mm": {"min": 4, "max": 6, "speed_m_per_min": 3.6,   "piercing_delay_s": 0.8},
    "8-12mm": {"min": 8, "max": 12, "speed_m_per_min": 2.5, "piercing_delay_s": 1.0},
    "14-18mm": {"min": 14, "max": 18, "speed_m_per_min": 1.6, "piercing_delay_s": 1.5},
    "20-25mm": {"min": 20, "max": 25, "speed_m_per_min": 1.2, "piercing_delay_s": 1.9},
    "30-40mm": {"min": 30, "max": 40, "speed_m_per_min": 0.8, "piercing_delay_s": 2.5},
    "45-60mm": {"min": 45, "max": 60, "speed_m_per_min": 0.6, "piercing_delay_s": 3.5},
}
# ----------------------------
# THICKNESS RANGES (mm)
# ----------------------------
THICKNESS_RANGES = {
    "1-3mm": {"min": 1, "max": 3},
    "4-6mm": {"min": 4, "max": 6},
    "8-12mm": {"min": 8, "max": 12},
    "14-18mm": {"min": 14, "max": 18},
    "20-25mm": {"min": 20, "max": 25},
    "30-40mm": {"min": 30, "max": 40},
    "45-60mm": {"min": 45, "max": 60},
}

# ----------------------------
# TASK 1: Total Tool Path Length
# ----------------------------
def calculate_entity_path_length(entity):
    try:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return math.dist(start, end)

        elif entity.dxftype() == 'ARC':
            radius = entity.dxf.radius
            angle_rad = math.radians(entity.dxf.end_angle - entity.dxf.start_angle)
            return abs(radius * angle_rad)

        elif entity.dxftype() == 'CIRCLE':
            return 2 * math.pi * entity.dxf.radius

        elif entity.dxftype() == 'LWPOLYLINE':
            points = list(entity.get_points())
            length = 0
            for i in range(len(points) - 1):
                x1, y1 = points[i][0], points[i][1]
                x2, y2 = points[i+1][0], points[i+1][1]
                length += math.dist((x1, y1), (x2, y2))
            return length

        elif entity.dxftype() == 'SPLINE':
            return entity.approximate_length()

        elif entity.dxftype() == 'ELLIPSE':
            a = entity.major_axis.magnitude / 2
            b = (entity.minor_axis.magnitude * entity.dxf.ratio) / 2
            h = ((a - b)**2) / ((a + b)**2)
            return math.pi * (a + b) * (1 + (3*h) / (10 + math.sqrt(4 - 3*h)))

    except Exception:
        return 0.0

    return 0.0

def calculate_total_tool_path_length(folder_path):
    total_path_length = 0.0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".dxf"):
            file_path = os.path.join(folder_path, filename)
            try:
                doc = ezdxf.readfile(file_path)
                msp = doc.modelspace()
                file_length = sum(calculate_entity_path_length(e) for e in msp)
                # print(f"{filename}: Tool Path Length = {file_length:.4f} meters")
                total_path_length += file_length
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nTotal Tool Path Length for all DXF files: {total_path_length:.4f} meters")
    return total_path_length

# ----------------------------
# TASK 1: COUNT DXF FILES
# ----------------------------
def count_dxf_files(folder_path):
    return len([f for f in os.listdir(folder_path) if f.lower().endswith('.dxf')])

# ----------------------------
# WIDTH CALCULATION
# ----------------------------
def get_units_factor(doc):
    insunits = doc.header.get('$INSUNITS', 0)
    return INSUNITS_TO_METERS.get(insunits, 1.0)

def get_entity_x_coords(entity):
    x_coords = []
    try:
        if entity.dxftype() == 'LINE':
            x_coords.extend([entity.dxf.start.x, entity.dxf.end.x])
        elif entity.dxftype() == 'CIRCLE':
            x, r = entity.dxf.center.x, entity.dxf.radius
            x_coords.extend([x - r, x + r])
        elif entity.dxftype() == 'ARC':
            x, r = entity.dxf.center.x, entity.dxf.radius
            x_coords.extend([x - r, x + r])
        elif entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
            for point in entity.get_points():
                x_coords.append(point[0])
        elif entity.dxftype() == 'SPLINE':
            for point in entity.control_points:
                x_coords.append(point.x)
        elif entity.dxftype() == 'ELLIPSE':
            x = entity.dxf.center.x
            r = max(abs(entity.major_axis.x), abs(entity.minor_axis.x)) * entity.dxf.ratio
            x_coords.extend([x - r, x + r])
    except Exception:
        pass
    return x_coords

def calculate_file_width_meters(dxf_path):
    try:
        doc = ezdxf.readfile(dxf_path)
        unit_factor = get_units_factor(doc)
        msp = doc.modelspace()

        all_x = []
        for entity in msp:
            all_x.extend(get_entity_x_coords(entity))

        if all_x:
            width = (max(all_x) - min(all_x)) * unit_factor
            return width
        else:
            return 0.0
    except Exception as e:
        print(f"Error reading {dxf_path} (width): {e}")
        return 0.0

def calculate_total_width_meters(folder_path):
    total_width = 0.0
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".dxf"):
            file_path = os.path.join(folder_path, filename)
            width = calculate_file_width_meters(file_path)
            # print(f"{filename}: Width = {width:.4f} meters")
            total_width += width
    print(f"\nTotal width of all DXF files: {total_width:.4f} meters\n")
    return total_width

# ----------------------------
# LENGTH CALCULATION
# ----------------------------
def calculate_entity_length(entity):
    try:
        if entity.dxftype() == 'LINE':
            start, end = entity.dxf.start, entity.dxf.end
            return (end - start).magnitude
        elif entity.dxftype() == 'CIRCLE':
            return 2 * math.pi * entity.dxf.radius
        elif entity.dxftype() == 'ARC':
            angle = math.radians(entity.dxf.end_angle - entity.dxf.start_angle)
            return abs(angle) * entity.dxf.radius
        elif entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
            points = [p[0:2] for p in entity.get_points()]
            return sum(math.dist(points[i], points[i+1]) for i in range(len(points)-1))
        elif entity.dxftype() == 'SPLINE':
            return entity.approximate_length()
        elif entity.dxftype() == 'ELLIPSE':
            a = entity.major_axis.magnitude / 2
            b = (entity.minor_axis.magnitude * entity.dxf.ratio) / 2
            h = ((a - b)**2) / ((a + b)**2)
            return math.pi * (a + b) * (1 + (3*h) / (10 + math.sqrt(4 - 3*h)))
    except Exception:
        pass
    return 0.0

def calculate_file_length_meters(dxf_path):
    try:
        doc = ezdxf.readfile(dxf_path)
        unit_factor = get_units_factor(doc)
        msp = doc.modelspace()

        total_length = 0.0
        for entity in msp:
            total_length += calculate_entity_length(entity)

        return total_length * unit_factor
    except Exception as e:
        print(f"Error reading {dxf_path} (length): {e}")
        return 0.0

def calculate_total_length_meters(folder_path):
    total_length = 0.0
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".dxf"):
            file_path = os.path.join(folder_path, filename)
            length = calculate_file_length_meters(file_path)
            # print(f"{filename}: Length = {length:.4f} meters")
            total_length += length
    print(f"\nTotal length of all DXF files: {total_length:.4f} meters\n")
    return total_length

# ----------------------------
# WEIGHT CALCULATION 
# ----------------------------
def calculate_weight(folder_path):
    quantity = count_dxf_files(folder_path)
    total_width = calculate_total_width_meters(folder_path)
    total_length = calculate_total_length_meters(folder_path)

    results = {}
    counter = 0

    for thickness_label, t_range in THICKNESS_RANGES.items():
        thickness_m = (t_range["min"] + t_range["max"]) / 2 / 1000  # mm to meters
        volume = total_width * total_length * thickness_m * quantity

        for material, density in DENSITIES.items():
            weight_kg = volume * density
            label = f"{thickness_label} for {material.replace('_', ' ').title()}"

            if weight_kg >= 1000:
                weight_ton = weight_kg / 1000
                print(f"{label} Weight is {weight_kg:,.0f} Kg ({weight_ton:.2f} Tons)")
                results[label] = {"kg": round(weight_kg), "tons": round(weight_ton, 2)}
            else:
                print(f"{label} Weight is {weight_kg:,.0f} Kg")
                results[label] = {"kg": round(weight_kg), "tons": 0}

            counter += 1
            if counter % 5 == 0:
                print()

    return results



def calculate_cutting_time(folder_path):
    total_path_length = calculate_total_tool_path_length(folder_path)  # in meters

    print("\nEstimated Cutting Time for All Thickness Ranges:\n")

    def minutes_to_hhmm(minutes):
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02}:{mins:02}"

    results = {}

    for label, props in THICKNESS_PROPERTIES.items():
        speed = props["speed_m_per_min"]
        pierce_delay_min = props["piercing_delay_s"] / 60  # seconds to minutes

        cut_time_min = total_path_length / speed
        total_time_min = cut_time_min + pierce_delay_min

        formatted_time = minutes_to_hhmm(total_time_min)
        results[label] = formatted_time

        print(f"{label}: {formatted_time}")

    return results

# ----------------------------
# Price Calculation in Euros
# ----------------------------
def get_price_per_kg(weight_kg):
    for limit in sorted(price_per_kg_by_weight):
        if weight_kg <= limit:
            return price_per_kg_by_weight[limit]
    return price_per_kg_by_weight[max(price_per_kg_by_weight)]

def get_cutting_price(thickness_mm, time_minutes):
    closest_thickness = min(cutting_price_by_thickness_and_time.keys(), key=lambda t: abs(t - thickness_mm))
    thresholds = [5, 10, 30, 60, 120, 180, 240, 300, 301]
    for i, limit in enumerate(thresholds):
        if time_minutes <= limit:
            return cutting_price_by_thickness_and_time[closest_thickness][i]
    return cutting_price_by_thickness_and_time[closest_thickness][-1]


def calculate_price_euros(folder_path):
    quantity = count_dxf_files(folder_path)
    total_width = calculate_total_width_meters(folder_path)
    total_length = calculate_total_length_meters(folder_path)
    total_path_length = calculate_total_tool_path_length(folder_path)

    weight_prices = {}
    cutting_prices = {}

    for thickness_label, t_range in THICKNESS_RANGES.items():
        avg_thickness = (t_range['min'] + t_range['max']) / 2
        thickness_m = avg_thickness / 1000
        volume = total_width * total_length * thickness_m * quantity

        for material, density in DENSITIES.items():
            weight_kg = volume * density
            price_per_kg = get_price_per_kg(weight_kg)
            weight_cost = weight_kg * price_per_kg
            key = f"{thickness_label} - {material.title().replace('_', ' ')}"
            weight_prices[key] = round(weight_cost, 2)

        speed = THICKNESS_PROPERTIES[thickness_label]['speed_m_per_min']
        pierce_delay = THICKNESS_PROPERTIES[thickness_label]['piercing_delay_s'] / 60
        cut_time = (total_path_length / speed) + pierce_delay
        cutting_price = get_cutting_price(avg_thickness, cut_time)
        cutting_prices[thickness_label] = cutting_price

    print("\n--- Material Cost in Euros ---")
    for k, v in weight_prices.items():
        print(f"{k}: €{v:,.2f}")

    print("\n--- Cutting Time Cost in Euros ---")
    for k, v in cutting_prices.items():
        print(f"{k}: €{v:,.2f}")

    return weight_prices, cutting_prices

def calculate_combined_price_euros(folder_path):
    weight_prices, cutting_prices = calculate_price_euros(folder_path)

    combined_totals = {}
    print("\n--- Combined Material + Cutting Cost in Euros ---")
    for thickness_label in THICKNESS_RANGES.keys():
        total_cutting = cutting_prices.get(thickness_label, 0)
        matching_weights = [v for k, v in weight_prices.items() if k.startswith(thickness_label)]
        total_material = sum(matching_weights)
        combined = total_cutting + total_material
        combined_totals[thickness_label] = round(combined, 2)
        print(f"{thickness_label}: €{combined:,.2f}")

    return combined_totals

# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    folder = "dxf files"  # Replace with your folder path

    print(f"\nTotal parts: {count_dxf_files(folder)}\n")

    # total_width = calculate_total_width_meters(folder)
    # total_length = calculate_total_length_meters(folder)
    # total_path_length = calculate_total_tool_path_length(folder)

    calculate_weight(folder)
    calculate_cutting_time(folder)
    calculate_price_euros(folder)
    calculate_combined_price_euros(folder)

