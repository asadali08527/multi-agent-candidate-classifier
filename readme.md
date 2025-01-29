# **HR Agent: Automated Email Job Application Classifier**  
This project automates the process of classifying job application emails, verifying their correctness, and sending replies. It reads unread emails, extracts relevant details (such as role, sender, and reply-to address), classifies the candidate's role using AI, and validates it against the subject line before automating the response. If the role doesn't match, manual intervention is required.

---

## **📁 Project Structure**  
```
📂 email_auto_classifier  
│── 📂 config                # Configuration files (API keys, credentials, etc.)  
│── 📂 scripts               # Core scripts for email processing and automation  
│   │── fetch_emails.py      # Fetch unread emails from Gmail API  
│   │── process_emails.py    # Process emails and classify job roles  
│   │── send_reply.py        # Send replies based on validated roles  
│── 📂 utils                 # Helper functions for email parsing and AI classification  
│   │── email_parser.py      # Extracts email content, sender, and reply-to address  
│   │── classifier.py        # Uses AI/ML to classify job roles based on email content  
│── 📂 logs                  # Stores logs of processed emails and errors  
│── 📂 templates             # Email templates for different job roles  
│── .env                     # API credentials (Do not share or commit this file)  
│── requirements.txt         # Python dependencies  
│── README.md                # Project documentation  
│── main.py                  # Entry point to start the email automation  
```

---

## **🚀 Features**  
✅ Fetches unread job application emails from Gmail API.  
✅ Extracts candidate details (email, subject, and reply-to addresses).  
✅ Uses OPENAI to classify candidate roles from email body and attachments.  
✅ Validates AI-classified roles against email subjects.  
✅ Automates replies if the classification is correct; otherwise, flags for manual review.  
✅ Sends emails to multiple recipients if needed.  
✅ Marks processed emails as "Read" to avoid duplication.  

---

## **🛠 Installation & Setup**  

### **1️⃣ Clone the Repository**  
```sh
git clone https://github.com/asadali08527/multi-agent-candidate-classifier.git
cd multi-agent-candidate-classifier
```

### **2️⃣ Create a Virtual Environment**  
```sh
python3 -m venv venv
source venv/bin/activate  # For MacOS/Linux
venv\Scripts\activate     # For Windows
```

### **3️⃣ Install Dependencies**  
```sh
pip install -r requirements.txt
```

### **4️⃣ Setup Gmail API Credentials**  
1. Go to the **[Google Cloud Console](https://console.cloud.google.com/)**  
2. Enable **Gmail API** for your project.  
3. Create **OAuth 2.0 Credentials** and download the `credentials.json` file.  
4. Place it inside the project **parent/** folder.  

### **5️⃣ Set Environment Variables**  
Create a `.env` file in the root directory and add:  
```
GOOGLE_APPLICATION_CREDENTIALS=config/credentials.json
EMAIL_SENDER=your-email@gmail.com
```

### **6️⃣ Authenticate Gmail API**  
Run the following command to authenticate your Gmail API:  
```sh
python scripts/authenticate.py
```
This will open a browser for you to sign in and grant permissions.

---

## **▶️ Running the Project**  

### **Fetch & Process Emails**  
```sh
python main.py
```
This script will:  
- Fetch unread job-related emails  
- Extract & classify job roles  
- Validate roles against email subjects  
- Send replies if valid  
- Mark processed emails as "Read"  

---

## **📚 Libraries Used & Why?**  

| Library        | Purpose  |  
|---------------|----------|  
| `google-auth` | Authentication for Gmail API |  
| `google-api-python-client` | Communicate with Gmail API |  
| `base64` | Decode email content |  
| `email` | Handle MIME email format |  
| `re` | Extract email addresses using regex |  
| `dotenv` | Manage API credentials securely |  
| `logging` | Log processed emails & errors |  

---

## **📝 Future Enhancements**  
🔹 Add AI-based NLP for better job role classification.  
🔹 Integrate database to store candidate details.  
🔹 Deploy as a cloud function for automatic execution.  

---

## **💡 Contributors**  
- **Asad Ali** ([GitHub](https://github.com/asadali08527))  
