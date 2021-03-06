#############################################################################################################
					***READ ME*** - Update_TBL
					      by Kevin Russell
#############################################################################################################

- The purpose of this project is to make the process of small-scale SQL table updates and small-scale SQL
table inserts more efficient, organized, systematic, and easier.

- This script will check validity of SQL table, user inputted table columns, table data types, table data
percision/size, table column non-null setting, and existence of table primary key ids. Additionally, the
script will check whether user provided multiple primary key columns.

- Items that do not pass the above checks will be processed into error excel spreadsheets that is exported
into the error log directory '03_Errors' located in the script's filepath. Tab Error_Details, in the error
file, will list the problematic issues with the other tabs.

- Updated items appended to a SQL table will have the old values and table's primary key appended to a shelf
file. This shelf file is stored under '04_Preserve' under current filepath. Data is appended to a dict
datatype that is under the key of the current datetime of YYYYMMDD.

- Script will log all actions it performs in print and in file, which is located in '01_Event_Logs' within
script's filepath.

- Script will check table if table has an edit date column, and script will automatically update that column
with the current datetime.

- A secondary script will export items from locker into an excel spreadsheet

- An excel vba spreadsheet is included to help users create excel worksheet templates for this python project


INSTALLATION:
	- Global.py can be placed in one of the PYTHONPATH directories or be placed in the same folder as
	Update_TBL.py.

	- Update_TBL.py needs to be placed in a new folder and you can place that folder where you see fit

	- Ensure that the following dependency modules are installed before running the python scripts
	(ie. pip install <module name>) [There may be additional dependency modules needed for installation]
		* Pandas
		* SQLAlchemy
		* Pyodbc
		* tkinter

SETUP:
	- Run Update_TBL.py

	- A prompt will ask for you to provide a directory to store the general settings. Generally you can
	use the script's pathway, but in other cases you may want to choose a different location. I like to
	keep my settings in a PYTHONPATH directory.

	- A prompt will inquire you to input your Server address/name and Database name. This will be saved
	in your general settings file.

HOW IT WORKS:
	- Format excel spreadsheet into the following format:
		* Filename can be whatever

		* Cell A1 must have [schema].[table name]

		* Tab must be named as Update_* or Insert_* (File can have multiple tabs)

		* Second row must have column names from SQL table. Primary Key must be included if your
		updating

		* Remaining cells below the column names is either the id of the primary key or new data
		that replaces the old data/inserts data in SQL

	- Place excel spreadsheet into '02_Process'

	- Execute Update_TBL.py

GRAB FROM PRESERVE LOCKER:
	- Run Shelf_Locker.py

	- Select a date from Preserve Locker to export into excel spreadsheet

	- Data will be exported into the '04_Preserve\Data_Locker_Export' directory of your script directory

	- Tab 'TAB_Details' show details of each tab for that day in the Locker

CUSTOMIZE TABLE SETTINGS FOR UPDATE_TBL.py
	- Run Shelf_Locker.py

	- Click settings button

	- Type SQL <schema>.<table>

	- *** Please keep in mind that an already added SQL table will load settings when you type in the
	<schema>.<table>

	- Select between enabling auto edit_dt update or disabling this feature

	- Change shelf life days for the SQL table
