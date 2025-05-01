# Tummi – Restaurant Review App

Tummi is a social restaurant review platform where users can:
- Write and manage reviews with notes, sentiment, and photos  
- Explore restaurants by filters (cuisine, price, location) via the Yelp API  
- Follow friends, like their posts, and view a feed of their reviews  
- Compare personal reviews for easy reflection  

---

## Setup Instructions (Mac/Linux)

### 1. Clone the Repository
```bash
git clone <repo-url>
cd <project-folder>
```

### 2. Create a Virtual Environment (optional)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install flask flask_sqlalchemy flask_jwt_extended requests
```

---

## API Keys

### Yelp API Key Required
This app uses the Yelp Fusion API to fetch restaurant data. 
A key is already included in the code, but to acquire your own key:

1. Visit: https://www.yelp.com/developers/v3/manage_app  
2. Sign in and create a new app to obtain an API key  
3. Replace the key in `app.py`:
```python
YELP_API_KEY = 'YOUR_API_KEY_HERE'
```

---

## Run the Code
Run:

```bash
python app.py
```

Visit your app in the browser at:  
http://localhost:5000

---