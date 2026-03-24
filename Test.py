<<<<<<< HEAD
import chardet

with open('Ammo.csv', 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
=======
import chardet

with open('Ammo.csv', 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
>>>>>>> origin/main
    print("Detected encoding:", result['encoding'], "with confidence:", result['confidence'])