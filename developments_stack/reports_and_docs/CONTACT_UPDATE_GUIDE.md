# 📇 BSVR Technologies — Contact & Identity Update Guide

This guide provides instructions on how to update official emails, phone numbers, GitHub usernames, and social media links across the **BSVR Technologies Website** ([https://www.bsvr.work/](https://www.bsvr.work/)) whenever contact details change.

---

## ⚡ Method 1: Automated 1-Command CLI (Recommended)

Run the automated synchronization script from the terminal:

```bash
# Update primary and secondary emails
python scripts/update_contact_info.py --email "contact@bsvr.work" --secondary-email "saivardhan@bsvr.work"

# Update phone number
python scripts/update_contact_info.py --phone "+91 8886244999"

# Update GitHub, Twitter/X, or Instagram handles
python scripts/update_contact_info.py --github "SVR1339" --twitter "Svreddy313" --instagram "svr_313"

# Or simply run without arguments for interactive step-by-step prompts:
python scripts/update_contact_info.py
```

After updating, deploy live to [https://www.bsvr.work/](https://www.bsvr.work/):
```bash
python scratch/deploy_all_updates.py
```

---

## 🛠️ Method 2: Single-Source-of-Truth in `website/index.html`

All identity references on the website are governed by a single configuration object located in `website/index.html` around line 2765:

```javascript
window.BSVR_CONTACT_CONFIG = {
  primaryEmail: "contact@bsvr.work",             // Official enterprise inquiries
  secondaryEmail: "saivardhan@bsvr.work",         // Direct executive channel
  personalEmail: "svreddy313.dev@gmail.com",     // Personal fallback
  directPhone: "+918886244999",                  // Click-to-call link
  phoneFormatted: "+91 88862 44999",             // Visual display
  location: "Hyderabad, India · London, United Kingdom",
  githubUser: "SVR1339",
  githubUrl: "https://github.com/SVR1339",
  twitterHandle: "Svreddy313",
  twitterUrl: "https://x.com/Svreddy313",
  instagramHandle: "svr_313",
  instagramUrl: "https://www.instagram.com/svr_313/",
  officialDomain: "https://www.bsvr.work"
};
```

Whenever you modify any field in this object, all interactive form submissions, mailto targets, and automated client interactions automatically adapt to your new credentials.

---

## 📋 Current Verified Official Credentials

| Channel | Verified Detail | Note |
| :--- | :--- | :--- |
| **Primary Domain Email** | `contact@bsvr.work` | Official inquiries & partnerships |
| **Direct Executive Email** | `saivardhan@bsvr.work` | Senior engineering & leadership |
| **Personal Email** | `svreddy313.dev@gmail.com` | Personal direct contact |
| **Executive Direct Line** | `+91 88862 44999` | Click-to-call direct line |
| **GitHub Organization** | [`github.com/SVR1339`](https://github.com/SVR1339) | Repositories & open source |
| **𝕏 (Twitter)** | [`@Svreddy313`](https://x.com/Svreddy313) | Announcements & network |
| **Instagram** | [`@svr_313`](https://www.instagram.com/svr_313/) | Direct community messaging |
| **Live Domain** | [`https://www.bsvr.work/`](https://www.bsvr.work/) | Verified production domain |
