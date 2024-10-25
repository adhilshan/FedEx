# FedEx Customer Care Dashboard

A web application for managing customer care operations, allowing customer service representatives to initiate calls, manage executive assignments, and track call statuses.

## Features

- Upload Excel files with customer phone numbers to initiate calls.
- Add new customer executives and cyber cell phone numbers.
- View ongoing call statuses in real time.
- DataTables integration for dynamic table views of customers and executives.
- Firebase for real-time database management.

## Technologies Used

- **Frontend:**
  - HTML
  - CSS
  - JavaScript
  - jQuery
  - DataTables

- **Backend:**
  - Flask (Python)
  - Firebase

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/customer-care-dashboard.git
   cd customer-care-dashboard
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Firebase:**
   - Create a Firebase project and set up a real-time database.
   - Update the Firebase configuration in the frontend code with your project's details.

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Open your browser and visit:**
   ```
   http://127.0.0.1:5000
   ```

## Usage

1. Use the "Select Excel File" button to upload an Excel file containing customer phone numbers.
2. Fill in the "Executive Phone Number" and "Cybercell Phone Number" fields to add new entries.
3. View ongoing calls and their statuses in the tables provided.

## Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [Firebase](https://firebase.google.com/)
- [DataTables](https://datatables.net/)
- [jQuery](https://jquery.com/)

### Instructions for Customization:
- **Replace `your-username`** in the clone URL with your actual GitHub username.
- Modify any sections to include specific instructions or features relevant to your project.
- Update the **Technologies Used** section to reflect any other libraries or frameworks you might be using.
- Ensure the **License** section matches the license you want to apply to your project.
