import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

print("✓ All libraries installed successfully!")
print("✓ You're ready to start!")

# Test API connection
print("\nTesting API connection...")
response = requests.get('https://api.mfapi.in/mf')
funds = response.json()
print(f"✓ API working! Found {len(funds)} mutual funds available")