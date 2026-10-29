# StudyOS: Student Study Analytics and Productivity System

StudyOS is a Python-based student productivity application that helps students manage academic subjects, assignments, and study sessions.

## Features
- Subject management
- Assignment management, filtering, and completion tracking
- Study-session logging
- Study statistics
- Subject-wise study-hour visualisation
- Weekly study-hour graph
- MySQL database integration

## Technologies
- Python
- MySQL Server
- MySQL Connector/Python
- Matplotlib
- Jupyter Notebook

## Requirements
Install Python and MySQL Server. Then install the Python libraries:

```bash
pip install -r requirements.txt
```

## How to run
1. Make sure MySQL Server is running on your computer.
2. Open `StudyOS.ipynb` in Jupyter Notebook or JupyterLab.
3. Run the notebook cells in order.
4. When prompted, enter your MySQL host, username, and password.
5. The application creates the `studyos` database and its tables if they do not already exist.

## Database
The application stores subjects, assignments, and study sessions in MySQL. The database is created locally when the program runs. The database itself is not included in this repository.

