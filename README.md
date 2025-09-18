# Job Portal Web Application

## 📌 Description
This is a Job Portal web application built with Flask (Python).
It provides two main roles: Job Seekers and Employers.
- Job Seekers (Users): Can register, log in, browse/search jobs, view details, apply by uploading resumes, and manage their profile.
- Employers: Can register, log in, post jobs, upload a company logo, manage profile, view applications, and download resumes.

---

## 🚀 Features

- 👤 **User Accounts**
  - Register and log in securely
  - Upload resumes and profile pictures
  - Apply for jobs and track applications

- 🏢 **Employer Accounts**
  - Register with organization details
  - Post new job openings
  - Manage and review job applications

- 💼 **Job Management**
  - Browse available jobs
  - View detailed job descriptions
  - Apply directly with uploaded resumes

- 🔐 **Authentication**
  - Secure password storage
  - Session management

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript (with templates in `templates/` folder)
- **Dependencies:** Listed in `requirements.txt`

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/vikram3192/Jobportal-web-application.git
cd Jobportal-web-application

### 2.Create & activate a virtual environment
```bash
python -m venv venv
Activate:
macOS / Linux: source venv/bin/activate
Windows: venv\Scripts\activate

### 3.Install dependencies
pip install -r requirements.txt

### 4.Configure environment variables
  1.Copy the example file:  
    cp .env.example .env
  2.Update .env with your own values
 

### 5. Set up the database
mysql -u root -p < schema.sql

### 6.Run the application
python app.py
