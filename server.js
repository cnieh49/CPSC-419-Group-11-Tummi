const express = require('express');
const bodyParser = require('body-parser');
const multer = require('multer');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public'))); // Serve static files

// Initialize SQLite database
const db = new sqlite3.Database('./reviews.db', (err) => {
  if (err) {
    console.error(err.message);
  } else {
    console.log('Connected to SQLite database.');

    // Create tables if they don't exist
    db.run(`
      CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_name TEXT NOT NULL,
        location TEXT NOT NULL,
        notes TEXT,
        photo_url TEXT,
        user_id INTEGER NOT NULL
      )
    `);
  }
});

// File upload setup
const storage = multer.diskStorage({
  destination: './uploads',
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  },
});
const upload = multer({ storage });

// Serve the main feed page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Submit a review endpoint
app.post('/reviews', upload.single('photo'), (req, res) => {
  const { restaurant_name, location, notes, user_id } = req.body;
  const photoPath = req.file ? req.file.path : null;

  const sql = `
    INSERT INTO reviews (restaurant_name, location, notes, photo_url, user_id)
    VALUES (?, ?, ?, ?, ?)
  `;
  db.run(sql, [restaurant_name, location, notes, photoPath, user_id], function (err) {
    if (err) {
      res.status(500).send({ error: err.message });
    } else {
      res.status(201).send({ message: 'Review submitted successfully!', reviewId: this.lastID });
    }
  });
});

// Fetch all reviews endpoint (to display on the main feed)
app.get('/reviews', (req, res) => {
  const sql = `SELECT * FROM reviews`;
  db.all(sql, [], (err, rows) => {
    if (err) {
      res.status(500).send({ error: err.message });
    } else {
      res.send(rows);
    }
  });
});

// Start server
app.listen(3000, () => console.log('Server running on http://localhost:3000'));
