import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional

class Emailer:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.sender_email = os.environ.get('EMAIL_ADDRESS')
        self.sender_password = os.environ.get('EMAIL_PASSWORD')
        
    def send_email(self, recipient_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email to a recipient
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Plain text email body
            html_body (str, optional): HTML email body
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS encryption
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_withdrawal_request_notification(self, user_email: str, user_name: str, points: float, amount: float, method: str) -> bool:
        """
        Send notification when a withdrawal request is submitted
        
        Args:
            user_email (str): User's email address
            user_name (str): User's full name
            points (float): Points being withdrawn
            amount (float): USD amount being withdrawn
            method (str): Withdrawal method
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Withdrawal Request Submitted - MyFigPoint"
        
        body = f"""
Hello {user_name},

We've received your withdrawal request for {points} points (${amount:.2f}) via {method}.

Your request is now being processed and will be completed within 24-48 hours. We'll notify you again when the withdrawal has been processed.

If you did not initiate this withdrawal request, please contact our support team immediately.

Thank you for using MyFigPoint!

Best regards,
The MyFigPoint Team
        """
        
        html_body = f"""
<html>
  <body>
    <h2>Hello {user_name},</h2>
    
    <p>We've received your withdrawal request for <strong>{points} points (${amount:.2f})</strong> via <strong>{method}</strong>.</p>
    
    <p>Your request is now being processed and will be completed within <strong>24-48 hours</strong>. We'll notify you again when the withdrawal has been processed.</p>
    
    <p><strong>If you did not initiate this withdrawal request, please contact our support team immediately.</strong></p>
    
    <p>Thank you for using MyFigPoint!</p>
    
    <br>
    <p>Best regards,<br>
    The MyFigPoint Team</p>
  </body>
</html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_withdrawal_approved_notification(self, user_email: str, user_name: str, points: float, amount: float, method: str) -> bool:
        """
        Send notification when a withdrawal request is approved
        
        Args:
            user_email (str): User's email address
            user_name (str): User's full name
            points (float): Points that were withdrawn
            amount (float): USD amount that was withdrawn
            method (str): Withdrawal method
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Withdrawal Approved - MyFigPoint"
        
        body = f"""
Hello {user_name},

Great news! Your withdrawal request for {points} points (${amount:.2f}) via {method} has been approved.

The funds are being processed and should arrive according to the timeline of your chosen payment method:
- Bank transfers: 1-3 business days
- PayPal: Within 24 hours
- Cryptocurrency: 1-2 hours
- Gift cards: Instant delivery

Thank you for using MyFigPoint!

Best regards,
The MyFigPoint Team
        """
        
        html_body = f"""
<html>
  <body>
    <h2>Hello {user_name},</h2>
    
    <p>Great news! Your withdrawal request for <strong>{points} points (${amount:.2f})</strong> via <strong>{method}</strong> has been <strong style="color: green;">approved</strong>.</p>
    
    <p>The funds are being processed and should arrive according to the timeline of your chosen payment method:</p>
    <ul>
      <li><strong>Bank transfers:</strong> 1-3 business days</li>
      <li><strong>PayPal:</strong> Within 24 hours</li>
      <li><strong>Cryptocurrency:</strong> 1-2 hours</li>
      <li><strong>Gift cards:</strong> Instant delivery</li>
    </ul>
    
    <p>Thank you for using MyFigPoint!</p>
    
    <br>
    <p>Best regards,<br>
    The MyFigPoint Team</p>
  </body>
</html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_withdrawal_rejected_notification(self, user_email: str, user_name: str, points: float, amount: float, method: str, reason: str = "not specified") -> bool:
        """
        Send notification when a withdrawal request is rejected
        
        Args:
            user_email (str): User's email address
            user_name (str): User's full name
            points (float): Points that were requested for withdrawal
            amount (float): USD amount that was requested for withdrawal
            method (str): Withdrawal method
            reason (str): Reason for rejection
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Withdrawal Request Rejected - MyFigPoint"
        
        body = f"""
Hello {user_name},

We regret to inform you that your withdrawal request for {points} points (${amount:.2f}) via {method} has been rejected.

Reason: {reason}

The points have been refunded to your account. If you believe this rejection was in error, please contact our support team.

Thank you for using MyFigPoint!

Best regards,
The MyFigPoint Team
        """
        
        html_body = f"""
<html>
  <body>
    <h2>Hello {user_name},</h2>
    
    <p>We regret to inform you that your withdrawal request for <strong>{points} points (${amount:.2f})</strong> via <strong>{method}</strong> has been <strong style="color: red;">rejected</strong>.</p>
    
    <p><strong>Reason:</strong> {reason}</p>
    
    <p>The points have been refunded to your account. If you believe this rejection was in error, please contact our support team.</p>
    
    <p>Thank you for using MyFigPoint!</p>
    
    <br>
    <p>Best regards,<br>
    The MyFigPoint Team</p>
  </body>
</html>
        """
        
        return self.send_email(user_email, subject, body, html_body)