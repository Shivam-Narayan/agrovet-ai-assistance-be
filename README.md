# agrovet-ai-assistance-backend django

# Backend Project Setup & Run Guide

Follow these steps to set up and run the backend project on your local system.

---

## 1️⃣ Create a folder for the project

Create an empty folder anywhere on your system. Example:  

```bash
mkdir agrovet-backend
cd agrovet-backend
```

---

## 2️⃣ (Optional but recommended) Create a virtual environment  

```bash
python -m venv .venv
```

---

## 3️⃣ Activate the virtual environment  

**Windows:**  
```bash
.venv\Scripts\activate
```  

**Linux / Mac:**  
```bash
source .venv/bin/activate
```

> You should see `(.venv)` at the start of your terminal prompt if activated successfully.

---

## 4️⃣ Clone the repository  

```bash
git clone https://github.com/Shivam-Narayan/agrovet-ai-assistance-be.git
```

---

## 5️⃣ Navigate to the backend folder  

```bash
cd backend
```

---

## 6️⃣ Install project dependencies  

```bash
pip install -r requirements.txt
```

---

## 7️⃣ Run database migrations (if applicable)  

```bash
python manage.py migrate
```

> Skip this step if migrations are already handled in `run.py`.

---

## 8️⃣ Start the backend application  

```bash
python run.py
```

> The backend should now be running! Open your browser or API client to test endpoints.

---

## 9️⃣ Common Errors & Fixes

1. **Python command not found**  
   - Make sure Python 3.11+ is installed.  
   - Check with:  
     ```bash
     python --version
     ```

2. **`pip` not recognized**  
   - Ensure pip is installed:  
     ```bash
     python -m ensurepip --upgrade
     ```

3. **Dependencies fail to install**  
   - Upgrade pip and retry:  
     ```bash
     python -m pip install --upgrade pip
     pip install -r requirements.txt
     ```

4. **Migration errors**  
   - Make sure the database is correctly configured in `settings.py` (if using Django).  
   - Try clearing previous migrations and re-running:  
     ```bash
     python manage.py makemigrations
     python manage.py migrate
     ```

5. **Virtual environment not activating**  
   - On Windows, ensure execution policy allows scripts:  
     ```bash
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

---

✅ **Tips for beginners:**  
- Always activate the virtual environment before running commands.  
- Use `deactivate` to exit the virtual environment when done.  
- Run commands from the backend folder (`backend`) unless specified otherwise.  
