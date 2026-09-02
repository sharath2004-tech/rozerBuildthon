# Integration Guide - Razorpay & Groq AI

## ✅ What's Now Working

### 1. **Sidebar Navigation** (All Pages)
- ✅ Fixed: Sidebar now visible on all pages
- ✅ Responsive: Mobile hamburger menu + desktop sidebar
- ✅ Navigation: Overview, At-Risk Revenue, Recovery Actions, Insights

### 2. **Razorpay Integration** (Real Payment Processing)
- ✅ Webhook handler: `/webhook/razorpay`
- ✅ Payment failure detection
- ✅ Automatic retry logic
- ✅ Payment link generation

### 3. **Groq AI Integration** (LLM-Powered Decisions)
- ✅ AI recommendations: `/ai/recommend`
- ✅ Model: Llama 3.3 70B (Groq's fastest)
- ✅ Real-time recovery suggestions
- ✅ Confidence scoring

---

## 🔑 Required API Keys

### **Backend Environment Variables (Render)**

```bash
# Database (already set)
DATABASE_URL=postgresql://...

# Razorpay (Required for real payments)
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_SECRET_KEY
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Groq AI (Required for LLM recommendations)
GROQ_API_KEY=gsk_YOUR_GROQ_KEY
```

### **Get Your API Keys:**

1. **Razorpay** (Free Test Mode)
   - Go to: https://dashboard.razorpay.com/signup
   - Navigate to: Settings → API Keys
   - Generate test keys (starts with `rzp_test_`)
   - Copy Key ID and Secret

2. **Groq** (Free Tier - Fast LLM)
   - Go to: https://console.groq.com/
   - Sign up (free)
   - Create API Key
   - Copy the key (starts with `gsk_`)

---

## 🚀 How to Test the Integrations

### **1. Check Service Status**

```bash
curl https://rozerbuildthon.onrender.com/services/status
```

**Expected Response:**
```json
{
  "services": {
    "database": {"database": "connected", "status": "ok"},
    "razorpay": {"configured": true, "status": "active"},
    "groq_ai": {
      "provider": "Groq",
      "model": "llama-3.3-70b-versatile",
      "configured": true,
      "status": "active"
    }
  },
  "version": "0.3.0"
}
```

---

### **2. Test AI Recommendation**

```bash
curl -X POST https://rozerbuildthon.onrender.com/ai/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_test123",
    "customer_id": "cust_456",
    "amount_inr": 2500.0,
    "rail": "UPI",
    "failure_code": "insufficient_funds",
    "lifetime_payments": 5,
    "lifetime_recoveries": 2,
    "hours_since_failure": 2.5
  }'
```

**Expected Response:**
```json
{
  "payment_id": "pay_test123",
  "ai_recommendation": {
    "action": "SEND_PAYMENT_LINK",
    "reason": "Customer has good history (2/5 recoveries). Insufficient funds suggests temporary issue. SMS payment link likely to succeed.",
    "confidence": 0.87,
    "alternate_action": "AUTO_RETRY"
  },
  "provider": "Groq",
  "model": "llama-3.3-70b-versatile"
}
```

---

### **3. Test Razorpay Webhook** (Simulated)

```bash
curl -X POST https://rozerbuildthon.onrender.com/webhook/razorpay \
  -H "Content-Type: application/json" \
  -d '{
    "event": "payment.failed",
    "payload": {
      "payment": {
        "entity": {
          "id": "pay_xyz789",
          "amount": 150000,
          "error_code": "BAD_REQUEST_ERROR",
          "contact": "+919876543210"
        }
      }
    }
  }'
```

**Expected Response:**
```json
{
  "message": "Payment failure logged",
  "payment_id": "pay_xyz789",
  "amount": 1500.0,
  "processed": true
}
```

---

## 🔗 Configure Razorpay Webhook (Production)

### **Step 1: Get Your Backend URL**
```
https://rozerbuildthon.onrender.com/webhook/razorpay
```

### **Step 2: Add Webhook in Razorpay Dashboard**

1. Go to: https://dashboard.razorpay.com/app/webhooks
2. Click **"Add New Webhook"**
3. **Webhook URL:** `https://rozerbuildthon.onrender.com/webhook/razorpay`
4. **Secret:** Use the same value as `RAZORPAY_WEBHOOK_SECRET` in Render
5. **Events to Track:**
   - ✅ payment.failed
   - ✅ payment.authorized (optional)
   - ✅ payment.captured (optional)
6. **Click "Create Webhook"**

Now real Razorpay events will hit your backend!

---

## 📊 What the Integrations Enable

### **With Razorpay:**
- ✅ Detect real payment failures in real-time
- ✅ Log failure reasons (insufficient funds, card declined, etc.)
- ✅ Automatic retry attempts
- ✅ Generate payment links for customers
- ✅ Track recovery success rates

### **With Groq AI:**
- ✅ AI-powered recovery recommendations
- ✅ Fast inference (< 1 second response)
- ✅ Context-aware decisions based on customer history
- ✅ Confidence scoring for each recommendation
- ✅ Fallback to rule-based if AI unavailable

---

## 🎯 Dashboard Features Now Working

1. **Overview** (`/`)
   - Real-time metrics from database
   - Recovery rate calculations
   - At-risk revenue tracking

2. **At-Risk Revenue** (`/at-risk`)
   - Payments needing attention
   - Queue for manual approval
   - Customer details

3. **Recovery Actions** (`/recovery-actions`)
   - AI-recommended actions
   - Batch processing results
   - Success/failure tracking

4. **Insights & Analytics** (`/insights`)
   - Compliance statistics
   - Rule performance
   - ROI calculations

---

## 🔧 Adding the Keys

### **In Render Dashboard:**

1. Go to: https://dashboard.render.com/
2. Select your web service: `revenue-recovery-backend`
3. **Environment** tab
4. **Add each key:**
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET` (make your own: `openssl rand -hex 32`)
   - `GROQ_API_KEY`
5. **Save Changes** (service will auto-restart)

---

## ✅ Verification Checklist

After adding keys, verify:

- [ ] Backend `/services/status` shows all services active
- [ ] `/ai/recommend` returns LLM recommendations (not error)
- [ ] `/webhook/razorpay` accepts POST requests
- [ ] Dashboard sidebar visible on all pages
- [ ] Frontend connects to backend (no localhost errors)

---

## 🎉 You're All Set!

Your AI Revenue Recovery Agent is now:
- ✅ Deployed on Render (backend) + Vercel (frontend)
- ✅ Using PostgreSQL for real data
- ✅ Integrated with Razorpay for payments
- ✅ Powered by Groq AI for smart recommendations
- ✅ Showing all 6 buildathon features

**Test URLs:**
- Frontend: https://rozer-buildthon.vercel.app/
- Backend: https://rozerbuildthon.onrender.com/
- Health: https://rozerbuildthon.onrender.com/health
- Status: https://rozerbuildthon.onrender.com/services/status
