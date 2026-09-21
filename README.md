# Capture Moments - AWS Powered Photographer Booking System

This is a full-stack Flask application that allows users to browse photographers, book them, and for administrators to manage photographer details. It uses MongoDB for data storage and AWS S3 for image hosting.

## Tech Stack

- **Frontend:** HTML5, CSS3 (Dark Theme), JavaScript
- **Backend:** Python (Flask)
- **Database:** MongoDB
- **Cloud Integration:** AWS S3 (image storage), optional SES for email confirmations

## Folder Structure

```
Capture Moments/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── sample_data.json
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/ (add images manually)
└── templates/
    ├── base.html
    ├── index.html
    ├── photographers.html
    └── admin.html
```

## Setup Instructions

1. **Clone the repository** (or copy files into a project directory).
2. **Create and activate a Python virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Copy `.env.example` to `.env` and fill in your credentials**:
   ```powershell
   copy .env.example .env
   # edit .env with your own keys
   ```
5. **Run MongoDB** locally or use a hosted service. Set `MONGO_URI` accordingly.
6. **(Optional) Create an AWS S3 bucket** and set the bucket name in `.env`.
   - Ensure the bucket has `public-read` policy or adjust the URL logic.
7. **Start the Flask server**:
   ```powershell
   python app.py
   ```

Visit `http://localhost:5000` in your browser.

## Sample MongoDB Schema

```
# photographers collection documents
{
  "_id": ObjectId(),
  "name": "Alice Smith",
  "specialization": "Wedding",
  "available_dates": ["2026-03-15", "2026-04-01"],
  "price": 1500.0,
  "rating": 4.8,
  "image_url": "https://your-bucket.s3.amazonaws.com/photographers/alice.jpg"
}

# bookings collection documents
{
  "_id": ObjectId(),
  "photographer_id": "<photographer ObjectId string>",
  "name": "Eve",
  "email": "eve@example.com",
  "phone": "1234567890",
  "event_date": "2026-03-15",
  "event_type": "Wedding"
}
```

You can import `sample_data.json` into MongoDB for initial testing.

## Features

- **Homepage** with hero and navigation
- **Photographer listing** with search and price filter
- **Booking form** with validation and duplicate check
- **Admin panel** to add/update/delete photographers and upload images
- **AWS S3 integration** for storing profile images
- **Optional SES email confirmations** (structure provided)

## Security Considerations

- Forms include basic required fields; additional validation can be added using WTForms.
- Duplicate booking prevention checks existing entry before saving.

## Next Steps / Improvements

- Add user authentication (login/register)
- Improve form validation with WTForms and Flask-WTF
- Use Blueprints for modularity
- Deploy on AWS EC2 or another host
- Add pagination to photographer listing

## License

This is an example project; adapt as needed.
