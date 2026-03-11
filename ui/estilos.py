# ui/estilos.py

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0a1628 0%, #0d2137 50%, #0a1628 100%);
    color: #e8f4f8;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1f35 0%, #0a1628 100%);
    border-right: 1px solid rgba(56,189,248,0.15);
}
.main-header {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(52,211,153,0.3);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative; overflow: hidden;
}
.main-header::before {
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(52,211,153,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.main-header h1 { color: #ecfdf5; font-size: 1.9rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
.main-header p  { color: #a7f3d0; margin: 0.4rem 0 0 0; font-size: 0.95rem; }

.metric-card {
    background: linear-gradient(135deg, rgba(15,30,55,0.9) 0%, rgba(10,22,40,0.9) 100%);
    border: 1px solid rgba(56,189,248,0.2); border-radius: 12px;
    padding: 1.2rem 1.4rem; text-align: center;
    transition: all 0.3s ease; backdrop-filter: blur(10px);
}
.metric-card:hover { border-color: rgba(52,211,153,0.4); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.metric-label { font-size: 0.75rem; color: #7dd3fc; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
.metric-value { font-size: 1.8rem; font-weight: 700; color: #ecfdf5; line-height: 1; font-family: 'DM Mono', monospace; }
.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.3rem; }

.section-header {
    color: #7dd3fc; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 2px;
    margin: 1.5rem 0 0.8rem 0; padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(56,189,248,0.2);
}
.info-box {
    background: rgba(56,189,248,0.08); border: 1px solid rgba(56,189,248,0.2);
    border-radius: 10px; padding: 1rem 1.2rem;
    font-size: 0.88rem; color: #bae6fd; margin: 0.8rem 0;
}
.alerta-stress {
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    border-radius: 10px; padding: 0.8rem 1.2rem;
    color: #fca5a5; font-size: 0.88rem; margin: 0.5rem 0;
}
.alerta-ok {
    background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.25);
    border-radius: 10px; padding: 0.8rem 1.2rem;
    color: #6ee7b7; font-size: 0.88rem; margin: 0.5rem 0;
}
.rinde-card {
    background: linear-gradient(135deg, rgba(5,46,22,0.8), rgba(6,78,59,0.8));
    border: 1px solid rgba(52,211,153,0.35); border-radius: 14px;
    padding: 1.5rem 2rem; margin: 0.8rem 0;
}
.rinde-valor { font-size: 2.4rem; font-weight: 700; color: #34d399; font-family: 'DM Mono', monospace; }
.rinde-rango { font-size: 0.85rem; color: #6ee7b7; margin-top: 0.3rem; }
.footer {
    text-align: center; color: #475569; font-size: 0.78rem;
    margin-top: 2rem; padding-top: 1rem;
    border-top: 1px solid rgba(56,189,248,0.1);
}
hr { border-color: rgba(56,189,248,0.15) !important; }
</style>
"""
