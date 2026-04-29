text = "Here is 📊 a chart! “Smart quotes” and a dash –. Bullet •."
print("Original:", text)
try:
    clean = text.encode('windows-1252', errors='ignore').decode('windows-1252')
    print("Cleaned:", clean)
except Exception as e:
    print("Error:", e)
