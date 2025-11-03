# Import/Export Accounts Feature - Implementation Guide

## Overview
A complete import/export feature has been added to allow admins to manage multiple accounts via Excel files.

## Features

### 1. **Export Accounts**
- Click "Download Accounts as Excel" on the Import/Export page
- Exports all user accounts with the following information:
  - Username
  - Email
  - Display Name
  - Role
  - Student Number (for students)
  - Course (for students)
  - Section (for students)
  - Institute (for faculty/coordinators/deans)
  - Date Joined

### 2. **Import Accounts**
- Upload an Excel file (.xlsx or .xls)
- The system reads the file and creates new accounts or updates existing ones
- Supported roles: Student, Faculty, Dean, Coordinator, Admin

## File Requirements

### Required Columns (Must be present)
1. **username** - Unique username for login
2. **email** - Email address
3. **password** - Initial password (for new accounts) or "***EXISTING***" to skip password update
4. **display_name** - Full name of the user
5. **role** - One of: Student, Faculty, Dean, Coordinator, Admin

### Optional Columns (Depends on role)

**For Students:**
- student_number - e.g., "22-1234" (supports dashes)
- course - e.g., BSCS, BSIS, ACT, BLIS
- section - Section code that already exists in the system (e.g., C102)

**For Faculty, Coordinator, Dean:**
- institute - Institute/Department name

## How to Use

### Export Process
1. Go to Admin Control Panel → Account Management → Import/Export Accounts
2. Click "Download Accounts as Excel"
3. File will be saved as "accounts_export.xlsx"
4. **The file is automatically sorted by role:**
   - 🟢 Students (Light Green)
   - 🔵 Faculty (Light Blue)
   - 🟠 Coordinators (Light Orange)
   - 🟣 Deans (Light Purple)
   - 🔴 Admins (Light Pink)
5. Each role group is color-coded for easy visual identification

### Import Process
1. Prepare your Excel file with required columns
2. Go to Admin Control Panel → Account Management → Import/Export Accounts
3. Click "Choose Excel File" and select your file
4. Click "Import Accounts"
5. Review the results:
   - Created: Number of new accounts created
   - Updated: Number of existing accounts updated
   - Skipped: Number of rows skipped due to errors

### Import Results
The system shows:
- ✅ Success count
- ⚠️ Any notes or warnings
- ❌ Any errors that occurred

## Example Data Format

| username | email | password | display_name | role | student_number | course | section | institute |
|----------|-------|----------|--------------|------|-----------------|--------|---------|-----------|
| john_doe | john@email.com | Pass123! | John Doe | Student | 22-1234 | BSCS | C102 | |
| jane_smith | jane@email.com | Pass456! | Jane Smith | Faculty | | | | College of Engineering |
| bob_coordinator | bob@email.com | Pass789! | Bob Johnson | Coordinator | | | | College of Science |

## Technical Details

### New Files Added
- `main/services/import_export_service.py` - Import/Export logic
- `main/templates/main/import_accounts.html` - Import/Export UI template
- New URLs: `/main/export-accounts/` and `/main/import-accounts/`
- New Views: `ExportAccountsView` and `ImportAccountsView`

### Dependencies
- openpyxl (for reading/writing Excel files)

### Security
- Admin only feature (Role check enforced)
- Activity logging for all imports/exports
- File format validation (only .xlsx and .xls accepted)

## Activity Logging
All import and export actions are logged in the Admin Activity Logs with:
- Timestamp
- Admin who performed the action
- Number of accounts affected
- IP address

## Error Handling
- Missing required columns → Import fails
- Invalid role → Row skipped, error logged
- Non-existent section code → Row skipped, error logged
- Duplicate username (update case) → Account updated instead
- Empty required fields → Row skipped

## Notes
- For updating existing accounts, use the exact same username
- Student numbers can contain dashes (e.g., 22-1234)
- All passwords should follow Django's default validation (minimum 8 characters recommended)
- Section codes must already exist in the system
- To skip password updates on existing accounts, use "***EXISTING***"
