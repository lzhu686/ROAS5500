"""Example: How to use the garbage classification server."""
import requests

# Send image to server
#Change the image path to the image you want to test
with open('data/battery.jpg', 'rb') as f:
    response = requests.post('http://10.4.0.3:8000/classify', files={'file': f})

# Print result
result = response.json()
print(f"Category: {result['category']}")

