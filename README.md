# MyFigPoint - Reward Points Platform

A full-featured reward points platform built with Flask and modern web technologies.

## Deployment to Render

This application is configured for deployment to Render with the included `render.yaml` file.

### Prerequisites
- A Render account (https://render.com)
- This repository

### Deployment Steps
1. Fork this repository to your GitHub account
2. Log in to your Render account
3. Click "New" and select "Web Service"
4. Connect your GitHub repository
5. Select the branch you want to deploy (usually main)
6. Render will automatically detect the `render.yaml` file and configure the deployment
7. Add the required environment variables:
   - `SECRET_KEY` - A random string for Flask security
   - `JWT_SECRET_KEY` - A random string for JWT token security
8. Click "Create Web Service"

### Environment Variables
The following environment variables should be set in your Render dashboard:

- `SECRET_KEY` - Flask secret key for sessions
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `DATABASE_URL` - Automatically provided by Render (via render.yaml)

### Default Admin User
After deployment, you can seed the database with test data by running the seed script:
```bash
python backend/seed.py
```

The default admin user credentials are:
- Email: admin@myfigpoint.com
- Password: MyFigPoint2025

## Local Development

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```

### Database Seeding
To seed the database with test data:
```bash
python backend/seed.py
```

## API Endpoints
- `/api/auth/login` - User login
- `/api/auth/register` - User registration
- `/api/tasks/` - Get available tasks
- `/api/users/` - User management
- And more...

## Frontend
The frontend is built with HTML, CSS (Tailwind), and JavaScript. All frontend files are served by the Flask backend.