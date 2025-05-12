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
pip install flask flask_sqlalchemy flask_jwt_extended requests dotenv sortedcontainers
```

---

## API Keys

### Yelp API Key Required
This app uses the Yelp Fusion API to fetch restaurant data.
To acquire your own key:

1. Visit: https://www.yelp.com/developers/v3/manage_app  
2. Sign in and create a new app to obtain an API key  
3. Create a file named `.env` in your project root and add the following line:
  YELP_API_KEY='YOUR_API_KEY_HERE'

---

## Files
The repository includes a pre-loaded database file named `db.sqlite`, which contains a few user accounts and data for testing purposes.

**Example test account:**
- Username: `ilovesushi@yale.edu`
- Password: `sushi`

If you’d like to start with a clean slate and create your own accounts, simply delete the `db.sqlite` file and run the app again. This will generate a fresh, empty database for you to use.

---

## Run the Code
Run:

```bash
python app.py
```

Visit your app in the browser at:  
http://localhost:5000

---

## Repository Structure

### Key Directories and Files

- **app.py**  
  Flask application containing all backend routes, API endpoints, and core feature logic
  
  Notable features: restaurant review system, comparison-based ranking, friending/following features, API integration, profile management
- **models.py**  
  Defines SQLAlchemy database models, including `User`, `Review`, and `Like`, as well as relationships for followers and review rankings
- **HTML Frontend Templates**
  - `login.html`: User login page
  - `register.html`: User registration page
  - `dashboard.html`: User dashboard and entry point
  - `feed.html`: User social feed with recent reviews and follow functionality
  - `profile.html` and `indiv_profile.html`: User profile pages
  - `compare_review.html`: Interface for review comparison and rankings
  - `explore.html`: Restaurant search and filter interface using Yelp API
  - `restaurant.html`: Restaurant information and reviews view