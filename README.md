# FinWise – Smart Personal Finance and Expense Management System

FinWise is a web application developed as a B.Tech Computer Science and Engineering major project. The main idea behind this project is to make personal finance management easier by bringing income, expenses, budgets and savings goals together in one place.

The application helps users keep track of their daily financial activities and understand where their money is going. It also provides a dashboard and charts to make financial information easier to understand.

## Features

- **User Authentication:** Users can register, log in and access their personal accounts.
- **Income Management:** Add and view different sources of income.
- **Expense Management:** Record daily expenses with amounts, dates and categories.
- **Budget Management:** Set monthly budgets and monitor spending.
- **Savings Goals:** Create savings targets and track progress.
- **Dashboard:** View important financial details, including income, expenses and balance.
- **Financial Analytics:** View charts showing income, expenses and category-wise spending.
- **CSV Export:** Download transaction records for future reference.
- **Guest Preview:** Explore the dashboard using sample information before creating an account.

## Technology Stack

| Part | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MongoDB Atlas, PyMongo |
| Frontend | HTML, CSS, JavaScript |
| UI Styling | Tailwind CSS |
| Charts | Chart.js |
| Environment Configuration | python-dotenv |
| Password Security | Werkzeug |

## Project Structure

The project is organised into separate frontend and backend folders to keep the interface and application logic easy to understand and maintain.

```text
SmartFin Manager/
│
├── frontend/
│   ├── templates/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── finance/
│   │   ├── macros/
│   │   └── base.html
│   │
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
│
├── backend/
│   └── app/
│       ├── models/
│       ├── routes/
│       ├── utils/
│       ├── __init__.py
│       ├── config.py
│       └── database.py
│
├── quality_checks/
│
├── venv/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

## Requirements

Before running the project, make sure you have:

- Python 3.10 or newer
- pip package manager
- MongoDB Atlas account or a local MongoDB installation
- VS Code or another code editor

## Installation and Setup

### 1. Open the project

Open the `SmartFin Manager` folder in VS Code.

### 2. Create a virtual environment

Open the VS Code terminal and run:

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install the required packages

```powershell
python -m pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the main project folder and add your configuration:

```env
SECRET_KEY=your_secret_key
MONGODB_URI=your_mongodb_connection_string
DB_NAME=finwise_db
FLASK_ENV=development
```

Replace the example values with your actual configuration.

**Important:** Do not upload your `.env` file or share your MongoDB credentials publicly.

## Running the Application

After completing the setup, start the application from the main project folder:

```powershell
python run.py
```

Once the Flask server starts, open your browser and visit:

```text
http://127.0.0.1:5000
```

You can then register a new account or explore the guest dashboard.

## Database

FinWise uses MongoDB to store user information, transactions, budgets and savings goals.

The application connects to MongoDB through PyMongo. The database connection settings are loaded from the `.env` file.

## Application Checks

The project includes Python files for checking important application features, such as authentication, transactions, savings goals and CSV export.

These checks help identify problems and verify that existing features continue to work after code changes.

Run the checks using the command configured for the project's current test setup.

## Security

Some important security practices followed in the project include:

- Passwords are stored using password hashing rather than plain text.
- Secret keys and database credentials are loaded through environment variables.
- User financial records should only be accessible to their respective owners.
- The `.env` file and virtual environment should not be uploaded to GitHub.

## Future Improvements

Some features that can be considered for future development include:

- More detailed financial reports.
- Better spending analysis.
- Automatic expense categorisation.
- Financial insights and expense predictions.
- Improved mobile experience.

## Project Information

**Project Name:** FinWise – Smart Personal Finance and Expense Management System

**Project Type:** B.Tech Computer Science and Engineering Major Project

The project is developed to provide a simple and convenient way to manage personal income, expenses, budgets and savings in one application.