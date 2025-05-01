# CNCB - DXF Cost & Geometry Analyzer

This Python script analyzes DXF files in a folder and computes:

- Total number of DXF files
- Total material width, length, and tool path length
- Estimated weight based on thickness, material density, and quantity
- CNC cutting time per thickness range
- Material price (€/kg based on tiered weights)
- Cutting cost (€/job based on time and thickness)
- Combined material + cutting price in Euros

---

## 📂 Folder Structure

Place all your `.dxf` files inside a folder. Update the `folder` variable in the script:

```python
folder = "dxf files"
