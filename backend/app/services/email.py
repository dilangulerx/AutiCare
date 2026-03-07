import resend
import os

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

TYPE_LABELS = {
    "medication": "💊 İlaç Hatırlatıcısı",
    "doctor": "🏥 Doktor Kontrolü",
    "therapy": "🧩 Terapi Seansı",
    "other": "🔔 Hatırlatıcı"
}

def send_reminder_email(to_email: str, child_name: str, title: str, description: str, reminder_type: str):
    type_label = TYPE_LABELS.get(reminder_type, "🔔 Hatırlatıcı")
    html = f"""
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;background:#FAFAF8;padding:40px;border-radius:12px;">
        <h1 style="color:#1a1a2e;font-weight:300;font-size:28px;">🌱 Gelişim Takip</h1>
        <div style="background:white;border-radius:12px;padding:32px;border-left:4px solid #FFB74D;margin-top:24px;">
            <p style="color:#666;font-size:12px;text-transform:uppercase;letter-spacing:2px;">{type_label}</p>
            <h2 style="color:#1a1a2e;font-weight:400;font-size:24px;">{title}</h2>
            <p style="color:#666;">Çocuk: <strong>{child_name}</strong></p>
            {f'<p style="color:#444;line-height:1.6;">{description}</p>' if description else ''}
        </div>
        <p style="color:#999;font-size:12px;text-align:center;margin-top:24px;">Gelişim Takip uygulaması tarafından gönderilmiştir.</p>
    </div>
    """
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"{type_label}: {title} — {child_name}",
        "html": html
    })