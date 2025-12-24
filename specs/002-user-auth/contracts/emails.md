# Email Templates Contract: User Authentication

**Version**: 1.0.0
**Date**: 2025-01-21
**Provider**: Resend

## Email Templates Overview

All emails use consistent branding and include:
- Header with application logo
- Primary action button (CTA)
- Security footer
- Unsubscribe link (for non-security emails)

## 1. Email Verification

**Template Name**: `email-verification`
**Subject**: Verify your email address for AI Book

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Verify your email</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .button {
      display: inline-block;
      padding: 12px 24px;
      background: #007bff;
      color: white;
      text-decoration: none;
      border-radius: 6px;
    }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Book</h1>
    </div>

    <h2>Welcome to AI Book!</h2>
    <p>Hi {{fullName}},</p>
    <p>Thank you for signing up! Please verify your email address to complete your registration.</p>

    <p style="text-align: center; margin: 30px 0;">
      <a href="{{verificationUrl}}" class="button">Verify Email Address</a>
    </p>

    <p>If you didn't create an account, you can safely ignore this email.</p>

    <div class="footer">
      <p><small>This link expires in 24 hours.</small></p>
      <p><small>If the button doesn't work, copy and paste this link:</small></p>
      <p><small>{{verificationUrl}}</small></p>
    </div>
  </div>
</body>
</html>
```

### Variables
- `fullName`: User's full name
- `verificationUrl`: Complete verification URL with token

## 2. Password Reset

**Template Name**: `password-reset`
**Subject**: Reset your password for AI Book

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Reset your password</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .button {
      display: inline-block;
      padding: 12px 24px;
      background: #dc3545;
      color: white;
      text-decoration: none;
      border-radius: 6px;
    }
    .alert {
      background: #f8d7da;
      color: #721c24;
      padding: 10px;
      border-radius: 4px;
      margin: 20px 0;
    }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Book</h1>
    </div>

    <h2>Reset Your Password</h2>
    <p>Hi {{fullName}},</p>
    <p>We received a request to reset your password for your AI Book account.</p>

    <div class="alert">
      <strong>Security Notice:</strong> If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
    </div>

    <p style="text-align: center; margin: 30px 0;">
      <a href="{{resetUrl}}" class="button">Reset Password</a>
    </p>

    <div class="footer">
      <p><small>This link expires in 1 hour.</small></p>
      <p><small>If the button doesn't work, copy and paste this link:</small></p>
      <p><small>{{resetUrl}}</small></p>
    </div>
  </div>
</body>
</html>
```

### Variables
- `fullName`: User's full name
- `resetUrl`: Complete password reset URL with token

## 3. Welcome Email (Post-Verification)

**Template Name**: `welcome`
**Subject**: Welcome to AI Book! Your account is verified

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Welcome to AI Book</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .button {
      display: inline-block;
      padding: 12px 24px;
      background: #28a745;
      color: white;
      text-decoration: none;
      border-radius: 6px;
    }
    .feature {
      background: #f8f9fa;
      padding: 15px;
      margin: 10px 0;
      border-radius: 6px;
    }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Book</h1>
    </div>

    <h2>Welcome to AI Book! 🎉</h2>
    <p>Hi {{fullName}},</p>
    <p>Your email has been successfully verified and your account is now active.</p>

    <h3>What you can do now:</h3>

    <div class="feature">
      <h4>💬 Chat with AI</h4>
      <p>Start conversations with our AI assistant about any topic.</p>
    </div>

    <div class="feature">
      <h4>📚 Save Your History</h4>
      <p>Your chat sessions are automatically saved and accessible anytime.</p>
    </div>

    <div class="feature">
      <h4>⚙️ Customize Your Experience</h4>
      <p>Set your preferences for themes, language, and chat settings.</p>
    </div>

    <p style="text-align: center; margin: 30px 0;">
      <a href="{{loginUrl}}" class="button">Start Chatting</a>
    </p>

    <div class="footer">
      <p><small>Have questions? Reply to this email and we'll be happy to help!</small></p>
      <p><small>You're receiving this email because you signed up for AI Book.</small></p>
    </div>
  </div>
</body>
</html>
```

### Variables
- `fullName`: User's full name
- `loginUrl`: URL to the login page

## 4. Security Alert

**Template Name**: `security-alert`
**Subject**: Security alert for your AI Book account

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Security Alert</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .alert {
      background: #fff3cd;
      color: #856404;
      padding: 15px;
      border-radius: 4px;
      margin: 20px 0;
      border-left: 4px solid #ffc107;
    }
    .details {
      background: #f8f9fa;
      padding: 15px;
      margin: 20px 0;
      border-radius: 6px;
    }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Book</h1>
    </div>

    <h2>Security Alert</h2>
    <p>Hi {{fullName}},</p>

    <div class="alert">
      <strong>Important:</strong> We detected a {{action}} on your account.
    </div>

    <h3>Activity Details:</h3>
    <div class="details">
      <p><strong>Action:</strong> {{action}}</p>
      <p><strong>Time:</strong> {{timestamp}}</p>
      <p><strong>IP Address:</strong> {{ipAddress}}</p>
      <p><strong>Device:</strong> {{userAgent}}</p>
      <p><strong>Location:</strong> {{location}}</p>
    </div>

    {{#if suspicious}}
    <div class="alert" style="background: #f8d7da; color: #721c24;">
      <strong>⚠️ This looks suspicious:</strong> If this wasn't you, please secure your account immediately.
      <p style="text-align: center; margin-top: 15px;">
        <a href="{{resetPasswordUrl}}" style="color: #721c24; text-decoration: underline;">Reset Your Password</a>
      </p>
    </div>
    {{/if}}

    <div class="footer">
      <p><small>If this was you, you can safely ignore this email.</small></p>
      <p><small>To review all account activity, visit your security settings.</small></p>
    </div>
  </div>
</body>
</html>
```

### Variables
- `fullName`: User's full name
- `action`: Description of security event
- `timestamp`: When the event occurred
- `ipAddress`: IP address of the request
- `userAgent`: Browser/device information
- `location`: Geographic location (if available)
- `suspicious`: Boolean flag for suspicious activity
- `resetPasswordUrl`: Link to reset password

## 5. Password Changed Confirmation

**Template Name**: `password-changed`
**Subject**: Your AI Book password has been changed

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Password Changed</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .success {
      background: #d4edda;
      color: #155724;
      padding: 15px;
      border-radius: 4px;
      margin: 20px 0;
      border-left: 4px solid #28a745;
    }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Book</h1>
    </div>

    <h2>Password Successfully Changed</h2>
    <p>Hi {{fullName}},</p>

    <div class="success">
      ✅ Your password for AI Book has been successfully changed.
    </div>

    <h3>Change Details:</h3>
    <p><strong>Time:</strong> {{timestamp}}</p>
    <p><strong>IP Address:</strong> {{ipAddress}}</p>
    <p><strong>Device:</strong> {{userAgent}}</p>

    <p>If you didn't make this change, please contact our support team immediately.</p>

    <div class="footer">
      <p><small>For your security, all other sessions have been logged out.</small></p>
    </div>
  </div>
</body>
</html>
```

### Variables
- `fullName`: User's full name
- `timestamp`: When the password was changed
- `ipAddress`: IP address of the request
- `userAgent`: Browser/device information

## Email Service Integration

### Resend Configuration

```typescript
// backend/src/services/email.ts

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

interface EmailData {
  to: string;
  subject: string;
  template: string;
  data: Record<string, any>;
}

export class EmailService {
  async sendEmail({ to, subject, template, data }: EmailData) {
    try {
      const result = await resend.emails.send({
        from: 'AI Book <noreply@ai-book.com>',
        to: [to],
        subject,
        html: await this.renderTemplate(template, data)
      });
      return { success: true, data: result };
    } catch (error) {
      console.error('Email send error:', error);
      return { success: false, error: error.message };
    }
  }

  private async renderTemplate(template: string, data: Record<string, any>) {
    // Use a template engine like Handlebars or simple string replacement
    const templates = {
      'email-verification': emailVerificationTemplate,
      'password-reset': passwordResetTemplate,
      'welcome': welcomeTemplate,
      'security-alert': securityAlertTemplate,
      'password-changed': passwordChangedTemplate
    };

    return templates[template](data);
  }
}
```

### Usage Examples

```typescript
// Send verification email
await emailService.sendEmail({
  to: user.email,
  subject: 'Verify your email address for AI Book',
  template: 'email-verification',
  data: {
    fullName: user.full_name,
    verificationUrl: `${process.env.FRONTEND_URL}/verify-email?token=${token}`
  }
});

// Send password reset email
await emailService.sendEmail({
  to: user.email,
  subject: 'Reset your password for AI Book',
  template: 'password-reset',
  data: {
    fullName: user.full_name,
    resetUrl: `${process.env.FRONTEND_URL}/reset-password?token=${token}`
  }
});
```

## Email Delivery Guidelines

1. **Security Headers**:
   - All links use HTTPS
   - Include SPF, DKIM, and DMARC records

2. **Content Guidelines**:
   - No JavaScript in emails
   - Inline CSS for compatibility
   - Alt text for all images
   - Plain text fallback

3. **Rate Limits**:
   - Max 10 emails per user per hour
   - Verification emails: 3 per day
   - Password reset: 5 per day

4. **Tracking**:
   - Delivery status monitoring
   - Open and click tracking (opt-in only)
   - Bounce handling and automatic cleanup

5. **Localization**:
   - Support for multiple languages
   - Time zone-aware timestamps
   - Localized date formats