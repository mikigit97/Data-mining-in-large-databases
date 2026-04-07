"""styles.py — CSS injected into the Streamlit app."""

CSS = """
/* ── Monospace SQL editor ── */
textarea[data-testid="stTextArea"] textarea {
    font-family: 'Courier New', Courier, monospace !important;
    font-size: 14px !important;
    background-color: #1e1e2e !important;
    color: #cdd6f4 !important;
    border: 1px solid #45475a !important;
    border-radius: 6px !important;
}

/* ── Story box: amber tint ── */
.story-box {
    background: linear-gradient(135deg, #2d2008 0%, #1a1209 100%);
    border-left: 4px solid #f9a825;
    border-radius: 6px;
    padding: 14px 18px;
    color: #fef3c7;
    font-style: italic;
    margin-bottom: 12px;
}

/* ── Task box: dark blue ── */
.task-box {
    background: #0d1b2a;
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 14px 18px;
    color: #e2e8f0;
    margin-bottom: 12px;
}

/* ── Solved banner ── */
.solved-banner {
    background: linear-gradient(90deg, #14532d, #166534);
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 12px 20px;
    color: #86efac;
    font-weight: bold;
    font-size: 18px;
    text-align: center;
    margin: 8px 0;
}

/* ── Error banner ── */
.error-banner {
    background: #2c0a0a;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 12px 20px;
    color: #fca5a5;
    font-size: 15px;
    margin: 8px 0;
}

/* ── Lock panel ── */
.lock-panel {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 32px;
    text-align: center;
    color: #6b7280;
    font-size: 16px;
    margin-top: 20px;
}

/* ── Badge shelf ── */
.badge-shelf {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
}
.badge-item {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 13px;
    color: #94a3b8;
}
.badge-item.earned {
    background: linear-gradient(135deg, #1e3a5f, #1e4d2b);
    border-color: #3b82f6;
    color: #93c5fd;
}

/* ── Story update box ── */
.story-update {
    background: #0c1a0c;
    border-left: 4px solid #22c55e;
    border-radius: 6px;
    padding: 12px 18px;
    color: #86efac;
    font-style: italic;
    margin-top: 10px;
}

/* ── Sidebar rank badge ── */
.rank-badge {
    background: linear-gradient(135deg, #1e3a5f, #2d1b4e);
    border: 2px solid #3b82f6;
    border-radius: 12px;
    padding: 10px 14px;
    text-align: center;
    margin-bottom: 8px;
}

/* ── Case closed badge in tab ── */
.case-badge {
    display: inline-block;
    background: #166534;
    color: #86efac;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 12px;
    margin-left: 8px;
}

/* ── Hot streak bar ── */
.streak-bar {
    background: linear-gradient(90deg, #7c2d12, #b45309);
    border-radius: 6px;
    padding: 6px 12px;
    color: #fef3c7;
    font-size: 14px;
    text-align: center;
    margin: 4px 0;
}

"""
