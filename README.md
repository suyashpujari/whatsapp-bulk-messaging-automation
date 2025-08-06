# 🚀 WhatsApp Bulk Messaging Automation Tool
![Status](https://img.shields.io/badge/status-Stable-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Selenium](https://img.shields.io/badge/selenium-4.x-orange)
![Maintained](https://img.shields.io/badge/maintained-yes-green)

> **Professional, robust, and compliant WhatsApp automation for sending messages to multiple contacts through your desktop.**

---

## 🎯 Features

- **Persistent Login** *(Scan QR only once)*
- **Bulk Messaging** *(CSV/Excel-based contacts list)*
- **Personalized Templates** *(dynamic fields in messages)*
- **Rate Limiting** *(human-like random delays)*
- **Interactive CLI** *(guided steps, progress bars)*
- **Advanced Logging** *(delivery stats, error diagnostics)*
- **Scheduling** *(send later with `schedule` library)*
- **Compliance Focused** *(consent, opt-out, privacy)*
- **Modular OOP Codebase** *(easy to extend or integrate)*

---

## 🛠️ Installation

```
git clone https://github.com/yourusername/whatsapp-bulk-automation.git
cd whatsapp-bulk-automation
pip install -r requirements.txt
```

Or individually:
```
pip install selenium webdriver-manager pandas openpyxl schedule
python whatsapp_bulk_automation_complete.py
```

---

## ⚙️ Quick Start

1. **Scan the QR code** (on first run; stays logged-in).
2. **Edit the generated contacts file** (`contacts_sample.csv` or `.xlsx`) with your phone numbers and message parameters (like `{name}`).
3. **Set your message template** (in code or via config).
4. **Confirm and begin**! Follow terminal instructions, progress is tracked transparently.

---

## 📝 Usage Sample

from whatsapp_bulk_automation import WhatsAppAutomation, Config

config = Config(
contacts_file='contacts.xlsx',
message_template='Hi {name}, your order is ready!',
delay_range=(3, 8), # in seconds
log_file='automation.log'
)

wa_bot = WhatsAppAutomation(config)
wa_bot.send_bulk_messages()

# Launch automation
wa_automator = WhatsAppAutomation(config)
wa_automator.send_bulk_messages()


### 📊 Supported Contact Files

- `contacts.csv`
- `contacts.xlsx` or `.xls`

*Sample file auto-generated on first run!*

---

## 🌟 Best Practices & Compliance

> **Respect user privacy and platform rules!**
- **Obtain explicit consent** from all recipients.
- **Include opt-out instructions** for every campaign.
- **Comply with WhatsApp’s Terms of Service** and local regulations (GDPR, CAN-SPAM, etc.).
- **Adjust delays and volume limits** to avoid account restrictions (suggested: ≤ 50 msgs/hr, ≤ 200 msgs/day).

---

## 🛡️ Legal Disclaimer

This project is for educational and legitimate business use only.  
Improper usage can lead to account bans or violate local regulations.  
Always secure user consent and avoid unsolicited messaging.

---

## 🤔 Troubleshooting

- **QR code keeps appearing?**  
  Make sure Chrome is not deleting user data on close and your script is running as Administrator.

- **Selector errors?**  
  WhatsApp Web updates its interface frequently. Update XPaths as needed in the configuration section.

- **Large lists slow to process?**  
  Split into smaller batches—avoid rapid sending to protect your account.


---

## 🔮 Roadmap

- [x] Persistent session support
- [x] CSV/Excel support
- [x] Message personalization
- [ ] WhatsApp Business API support
- [ ] Telegram/Signal integration
- [ ] AI-powered templates and analytics

*Want to contribute? PRs are welcome!*

---

## 🙏 Acknowledgments

- [Selenium](https://selenium.dev/)
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- [pandas](https://pandas.pydata.org/)

Project inspired by the needs of responsible communication.

---

## 📬 Contact & Community

🤝 For support, collaboration, or questions, open a GitHub Issue or start a Discussion!

---

## ⭐️ Star This Repo!

If you find this project helpful, please ⭐ it on GitHub—it helps others discover and fosters community!

---
