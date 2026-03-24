import chardet

with open('Ammo.csv', 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
    print("Detected encoding:", result['encoding'], "with confidence:", result['confidence'])