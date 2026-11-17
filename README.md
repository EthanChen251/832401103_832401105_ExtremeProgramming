# ContactHub · Contact Manager

ContactHub is the Extreme Programming project for the FZU–MU Software Engineering course. Each account has a private address book. You can keep several phone numbers for one person, pin frequent contacts, and move an address book between the application and an Excel workbook.

[Open the application on Tencent Cloud](http://43.128.135.64/)

## Features

- Register, sign in, and sign out. The first visit opens in English. Use the language button in the header to switch between English and Chinese.
- Create, view, edit, or delete a contact. Record notes and any combination of phone numbers, email addresses, addresses, QQ handles, WeChat accounts, and websites.
- Pin favorites at the top of the directory or open the Favorites view. Search by name, contact detail, or note. Matching text is highlighted, and individual contact details can be copied.
- Download a blank Excel template, import contacts, or export the complete address book. Import errors identify the affected rows and columns when available.

## Technology

Vue 3 renders the interface and Vite builds it. During development, Vite forwards requests under `/api` to the Flask server. Flask uses SQLite for persistent account and contact data, and openpyxl for Excel files.

## Run locally on Windows

Install Git, Python 3.13, and Node.js 22.12 or later. The project has been exercised with Python 3.13 and Node.js 24. Run these commands in PowerShell.

```powershell
git clone https://github.com/EthanChen251/832401103_832401105_ExtremeProgramming.git
cd 832401103_832401105_ExtremeProgramming
```

In the first terminal, start Flask from the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app contact_manager run --host 127.0.0.1 --port 5000
```

Leave Flask running. In a second terminal, start Vite from the repository root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

If the npm mirror in the lockfile is unavailable, install the same locked dependencies from the official registry:

```powershell
npm.cmd ci --registry=https://registry.npmjs.org/ --replace-registry-host=registry.npmmirror.com
```

Open the [local address book](http://127.0.0.1:5173/) and select **Create an account**. The server creates its account and contact databases in `backend/instance/` as needed. Data persists after a restart. To build the frontend for deployment, run `npm.cmd run build` from `frontend/`; the output is in `frontend/dist/`.

## Excel format

Choose **Download Excel template** to obtain the seven column headers in a sheet named `Contacts`. Use one row per person. To enter two phone numbers for the same person, put both in the `phones` cell on separate lines. The template formats text columns as text so leading zeros survive. A successful import appends rows; importing the same workbook twice adds the contacts twice.

## Code and interface conventions

- Vue sends relative requests under `/api/v1`. Display labels can change language; JSON field names and Excel headers stay stable.
- The server generates contact IDs and timestamps. A partial edit sends only changed fields. Sending `methods` replaces the complete list of contact methods.
- The backend validates incoming contact fields before writing to SQLite. Workbook errors can include a row, a field, and a message for each issue.
- Phone numbers and identifiers travel as strings. Preserve their leading zeros, symbols, and the order of values within a method type.

See the [API and data specification](API_SPEC.md) for exact field names, validation rules, and response examples.

## Project documents

- [API and data specification](API_SPEC.md)
- [Project plan in English](docs/XP_Contact_Manager_Project_Plan_EN.md)
- [Project plan in Chinese](docs/XP_Contact_Manager_Project_Plan_CN.md)
