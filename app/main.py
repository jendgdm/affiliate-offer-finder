"""Main Streamlit application for Affiliate Offer Finder."""
import streamlit as st
import pandas as pd
import html
import re
from services.aggregator import OfferAggregator
from config import Config

# Page config
st.set_page_config(
    page_title="Affiliate Offer Finder",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bootstrap CSS + Custom styling
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<style>
    /* Bootstrap integration */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main container */
    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* Main title styling */
    h1 {
        color: #2563eb;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Card styling with Bootstrap look */
    .offer-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        display: block;
        text-decoration: none;
        color: inherit;
        cursor: pointer;
    }

    .offer-card:hover {
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        transform: translateY(-2px);
        border-color: #2563eb;
        text-decoration: none;
    }

    .offer-card .card-title {
        color: #1e293b;
        font-size: 20px;
        font-weight: 700;
        line-height: 1.3;
    }

    .offer-card:hover .card-title {
        color: #2563eb;
    }

    /* Badge styling */
    .custom-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .badge-primary {
        background-color: #dbeafe;
        color: #1e40af;
    }

    .badge-success {
        background-color: #d1fae5;
        color: #065f46;
    }

    .badge-info {
        background-color: #e0e7ff;
        color: #4338ca;
    }

    .badge-warning {
        background-color: #fef3c7;
        color: #92400e;
    }

    /* Commission badge */
    .commission-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 24px;
        font-weight: 700;
        font-size: 15px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        text-align: center;
        white-space: nowrap;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 14px 28px;
        border: none;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
        font-size: 16px;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        transform: translateY(-2px);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        border-right: 1px solid #e2e8f0;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        padding-top: 0 !important;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* Links */
    a {
        color: #2563eb;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s ease;
    }

    a:hover {
        color: #1d4ed8;
        text-decoration: none;
    }

    /* Number badge */
    .number-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border-radius: 8px;
        font-weight: 700;
        font-size: 14px;
        margin-right: 12px;
    }

    /* Category icon */
    .category-icon {
        font-size: 28px;
        opacity: 0.9;
    }

    /* Description text */
    .offer-description {
        color: #64748b;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 12px;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .offer-card {
            padding: 16px;
        }

        .commission-badge {
            font-size: 13px;
            padding: 8px 16px;
        }

        .number-badge {
            width: 28px;
            height: 28px;
            font-size: 12px;
        }

        h1 {
            font-size: 32px !important;
        }
    }

    /* Loading animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .offer-card {
        animation: fadeIn 0.4s ease-out;
    }

    /* Modal overlay */
    .search-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeInModal 0.3s ease-out;
    }

    @keyframes fadeInModal {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    .search-modal-content {
        background: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        text-align: center;
        max-width: 400px;
        animation: slideUp 0.3s ease-out;
    }

    @keyframes slideUp {
        from {
            transform: translateY(30px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    .modal-spinner {
        width: 60px;
        height: 60px;
        border: 4px solid #e5e7eb;
        border-top: 4px solid #2563eb;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .modal-title {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 12px;
    }

    .modal-subtitle {
        font-size: 14px;
        color: #64748b;
        line-height: 1.6;
    }
</style>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
""", unsafe_allow_html=True)

# Helper function to strip HTML tags
def strip_html_tags(text):
    """Remove HTML tags from text."""
    if not text:
        return text
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

# Initialize aggregator (cached so Google Sheets connection is reused across reruns)
@st.cache_resource
def get_aggregator():
    """Initialize and cache the aggregator."""
    return OfferAggregator()

def main():
    """Main application."""

    # ------------------------------------------------------------------
    # Google OAuth Login Gate (skip if not configured)
    # ------------------------------------------------------------------
    user_name = None
    user_email = None

    if Config.is_oauth_configured():
        from streamlit_google_auth import Authenticate

        authenticator = Authenticate(
            secret_credentials_path=Config.GOOGLE_OAUTH_CLIENT_JSON,
            cookie_name='aff_finder_auth',
            cookie_key=Config.COOKIE_SECRET,
            redirect_uri=Config.OAUTH_REDIRECT_URI,
        )
        authenticator.check_authentification()

        if not st.session_state.get('connected'):
            # Show login page
            st.markdown("""
            <div style="text-align: center; padding: 80px 20px;">
                <h1 style="font-size: 48px; margin-bottom: 16px; color: #2563eb; font-weight: 700;">
                    <i class="bi bi-cash-coin"></i> Affiliate Offer Finder
                </h1>
                <p style="font-size: 18px; color: #64748b; margin-bottom: 40px;">
                    Sign in with your company email to continue
                </p>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                authenticator.login()
            st.stop()

        # Check email domain restriction
        user_email = st.session_state['user_info'].get('email', '')
        user_name = st.session_state['user_info'].get('name', '')

        if Config.ALLOWED_EMAIL_DOMAINS:
            email_domain = user_email.split('@')[-1] if '@' in user_email else ''
            if email_domain not in Config.ALLOWED_EMAIL_DOMAINS:
                allowed = ', '.join(f'@{d}' for d in Config.ALLOWED_EMAIL_DOMAINS)
                st.error(f"Access restricted to {allowed} emails. You signed in as {user_email}.")
                if st.button("Sign out"):
                    authenticator.logout()
                st.stop()

    # Hero section with Bootstrap styling
    st.markdown("""
    <div style="text-align: center; padding: 30px 0 40px 0;">
        <h1 style="font-size: 48px; margin-bottom: 16px;">
            <i class="bi bi-cash-coin" style="color: #2563eb;"></i> Affiliate Offer Finder
        </h1>
        <p style="font-size: 18px; color: #64748b; font-weight: 500;">
            Discover profitable affiliate programs for your niche with commission details
        </p>
    </div>
    """, unsafe_allow_html=True)

    aggregator = get_aggregator()

    # =====================================================================
    # TEMPORARY: Floating Chat Feedback (remove this block when no longer needed)
    # =====================================================================
    # =====================================================================
    # END: Floating Chat Feedback
    # =====================================================================

    # Sidebar - Configuration & Filters
    with st.sidebar:
        # Logo/Header
        st.markdown("""
        <div style="text-align: center; padding: 0 0 8px 0; border-bottom: 2px solid #e2e8f0; margin: 0 0 8px 0;">
            <h2 style="color: #2563eb; margin: 0; font-size: 20px;">
                <i class="bi bi-funnel"></i> Filters
            </h2>
        </div>
        """, unsafe_allow_html=True)

        # Mode Selection
        search_mode = st.radio(
            "Search Mode",
            options=["All", "Direct", "Blog Post"],
            index=0,
            help="All = Show everything | Direct = Direct brand affiliate programs | Blog Post = Articles listing multiple programs",
            horizontal=True
        )

        keyword = st.text_input(
            "Niche/Keyword",
            placeholder="e.g., VPN, hosting, software",
            help="Enter your niche"
        )

        limit = st.number_input("Max Results", min_value=5, max_value=200, value=50, step=5)

        search_triggered = st.button("🔎 Search Offers", type="primary", use_container_width=True)
        force_refresh = st.button("🔄 Force Refresh", help="Bypass cache", use_container_width=True)

        # User info & logout (if logged in)
        if user_name:
            st.markdown("---")
            st.markdown(f"**{user_name}**  \n{user_email}")
            if st.button("Sign out", use_container_width=True):
                authenticator.logout()

        # (Feedback form moved to floating chat bubble)

    # Main content header
    st.markdown('<h2 style="color: #1e293b; font-weight: 700; margin-bottom: 24px;"><i class="bi bi-grid-3x3-gap"></i> Search Results</h2>', unsafe_allow_html=True)

    # Detect keyword change — only re-fetch when keyword changes (not mode)
    if 'previous_keyword' in st.session_state and st.session_state.previous_keyword != keyword:
        if 'all_offers' in st.session_state:
            del st.session_state.all_offers
    st.session_state.previous_keyword = keyword

    # Fetch all offers once, then filter by mode (mode change = instant, no re-fetch)
    need_fetch = search_triggered or force_refresh or 'all_offers' not in st.session_state

    if need_fetch:
        # Show loading spinner immediately while data loads
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; padding: 60px 20px;">
            <div style="text-align: center;">
                <div style="width: 50px; height: 50px; border: 4px solid #e5e7eb; border-top: 4px solid #2563eb;
                            border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px;"></div>
                <p style="color: #475569; font-size: 16px; font-weight: 500;">Loading offers...</p>
            </div>
        </div>
        <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
        """, unsafe_allow_html=True)

        all_offers = aggregator.search_discovery_networks(
            keyword=keyword if keyword else None,
            limit=limit * 2,
            analyze_potential=True,
            force_refresh=force_refresh
        )

        st.session_state.all_offers = all_offers
        loading_placeholder.empty()

    # Filter by mode from in-memory cache (instant, no API/sheets call)
    all_offers = st.session_state.get('all_offers', [])
    if search_mode == "Direct":
        offers = [o for o in all_offers if o.category == "Direct Brand"]
    elif search_mode == "Blog Post":
        offers = [o for o in all_offers if o.category == "Blog Post"]
    else:
        offers = all_offers
    offers = offers[:limit]
    st.session_state.offers = offers
    st.session_state.search_mode = search_mode

    # Display results
    if 'offers' in st.session_state and st.session_state.offers:
        offers = st.session_state.offers
        mode = st.session_state.get('search_mode', 'Direct')

        # Results summary with Bootstrap alerts
        if mode == "Direct":
            st.markdown(f"""
            <div class="alert alert-info" role="alert" style="border-left: 4px solid #2563eb; background-color: #eff6ff; border-radius: 8px; padding: 16px;">
                <strong><i class="bi bi-bullseye"></i> Direct Brands:</strong> Found {len(offers)} direct affiliate programs. Click to apply!
            </div>
            """, unsafe_allow_html=True)
        elif mode == "Blog Post":
            st.markdown(f"""
            <div class="alert alert-info" role="alert" style="border-left: 4px solid #7c3aed; background-color: #faf5ff; border-radius: 8px; padding: 16px;">
                <strong><i class="bi bi-newspaper"></i> Blog Posts:</strong> Found {len(offers)} articles with multiple affiliate programs!
            </div>
            """, unsafe_allow_html=True)
        elif mode == "All":
            direct_count = len([o for o in offers if o.category == "Direct Brand"])
            blog_count = len([o for o in offers if o.category == "Blog Post"])
            st.markdown(f"""
            <div class="alert alert-success" role="alert" style="border-left: 4px solid #10b981; background-color: #f0fdf4; border-radius: 8px; padding: 16px;">
                <strong><i class="bi bi-check-circle"></i> Success:</strong> Found {len(offers)} offers total
                ({direct_count} direct brands 🎯 + {blog_count} blog posts 📰)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"Found {len(offers)} offers")

        # Show last updated date
        if aggregator.sheets_cache:
            effective_kw = keyword if keyword else "software"
            try:
                last_updated = aggregator.sheets_cache.get_last_updated(effective_kw)
                if last_updated:
                    st.caption(f"Last updated: {last_updated.strftime('%B %d, %Y')}")
            except Exception:
                pass

        # Build all cards in one HTML block to avoid Streamlit containers
        all_cards_html = '<div>'

        for idx, offer in enumerate(offers[:limit], 1):
            # Determine the link URL
            safe_url = html.escape(offer.tracking_url) if offer.tracking_url else "#"

            # Build card HTML - wrap entire card in anchor tag
            if offer.tracking_url:
                all_cards_html += f'<a href="{safe_url}" target="_blank" class="offer-card">'
            else:
                all_cards_html += '<div class="offer-card" style="cursor: default;">'

            all_cards_html += '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">'

            # Left side
            all_cards_html += '<div style="flex: 1; min-width: 0;">'

            # Title row
            all_cards_html += '<div style="display: flex; align-items: center; margin-bottom: 12px;">'
            all_cards_html += f'<span class="number-badge">{idx}</span>'

            clean_name = strip_html_tags(offer.name)
            safe_name = html.escape(clean_name)
            all_cards_html += f'<span class="card-title">{safe_name}</span>'

            all_cards_html += '</div>'

            # Badges row
            all_cards_html += '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'

            clean_advertiser = strip_html_tags(offer.advertiser_name)
            safe_advertiser = html.escape(clean_advertiser)
            all_cards_html += f'<span class="custom-badge badge-primary"><i class="bi bi-building"></i> {safe_advertiser}</span>'

            if offer.category == "Direct Brand":
                all_cards_html += '<span class="custom-badge badge-success"><i class="bi bi-bullseye"></i> Direct Brand</span>'
            else:
                all_cards_html += '<span class="custom-badge badge-info"><i class="bi bi-newspaper"></i> Blog Post</span>'

            if offer.network:
                clean_network = strip_html_tags(offer.network)
                safe_network = html.escape(clean_network)
                all_cards_html += f'<span class="custom-badge badge-warning"><i class="bi bi-diagram-3"></i> {safe_network}</span>'

            all_cards_html += '</div>'
            all_cards_html += '</div>'  # Close left side

            # Right side: Commission badge + Potential score
            all_cards_html += '<div style="margin-left: 20px; flex-shrink: 0; display: flex; flex-direction: column; gap: 8px; align-items: flex-end;">'

            # Commission badge
            if offer.category == "Direct Brand" and offer.commission_value:
                if offer.commission_type == "Percentage":
                    all_cards_html += f'<div class="commission-badge"><i class="bi bi-cash-coin"></i> {int(offer.commission_value)}%</div>'
                elif offer.commission_type == "Fixed":
                    all_cards_html += f'<div class="commission-badge"><i class="bi bi-currency-dollar"></i> ${int(offer.commission_value)}</div>'
            else:
                if offer.category == "Direct Brand":
                    all_cards_html += '<span class="category-icon">🎯</span>'
                else:
                    all_cards_html += '<span class="category-icon">📰</span>'

            all_cards_html += '</div>'

            all_cards_html += '</div>'  # Close flex container

            # Description INSIDE the card (unified with card styling)
            if offer.description:
                clean_desc = strip_html_tags(offer.description)
                desc = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
                safe_desc = html.escape(desc)
                all_cards_html += f'<div style="margin-top: 16px;"><p style="color: #64748b; font-size: 14px; line-height: 1.6; margin: 0;">{safe_desc}</p></div>'

            # Scalability Metrics
            if offer.scalability_score is not None:
                all_cards_html += '<div style="margin-top: 16px; padding: 12px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 8px; border-left: 3px solid #3b82f6;">'

                # Scalability score header
                score_color = "#10b981" if offer.scalability_score >= 75 else "#f59e0b" if offer.scalability_score >= 50 else "#ef4444"
                all_cards_html += f'<div style="margin-bottom: 10px;"><span style="color: #1e293b; font-size: 13px; font-weight: 700;"><i class="bi bi-graph-up-arrow"></i> Scalability:</span> <span style="color: {score_color}; font-weight: 700; font-size: 14px;">{offer.scalability_score}/100</span></div>'

                # Metrics grid
                all_cards_html += '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px;">'

                # Row 1
                if offer.traffic_monthly:
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-globe" style="color: #3b82f6;"></i> Traffic: <span style="font-weight: 600;">{html.escape(offer.traffic_monthly)}</span></div>'

                if offer.cookie_duration:
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-clock" style="color: #8b5cf6;"></i> Cookie: <span style="font-weight: 600;">{offer.cookie_duration} days</span></div>'

                if offer.growth_percentage:
                    growth_color = "#10b981" if offer.growth_percentage.startswith('+') else "#ef4444"
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-graph-up" style="color: {growth_color};"></i> Growth: <span style="font-weight: 600; color: {growth_color};">{html.escape(offer.growth_percentage)}</span></div>'

                # Row 2
                if offer.competition_level:
                    comp_color = "#10b981" if offer.competition_level in ["Low", "Very Low"] else "#f59e0b" if offer.competition_level == "Medium" else "#ef4444"
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-bullseye" style="color: {comp_color};"></i> Competition: <span style="font-weight: 600; color: {comp_color};">{html.escape(offer.competition_level)}</span></div>'

                if offer.domain_authority:
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-award" style="color: #f59e0b;"></i> DA: <span style="font-weight: 600;">{offer.domain_authority}/100</span></div>'

                if offer.instagram_followers:
                    all_cards_html += f'<div style="color: #475569;"><i class="bi bi-instagram" style="color: #ec4899;"></i> IG: <span style="font-weight: 600;">{html.escape(offer.instagram_followers)}</span></div>'

                all_cards_html += '</div>'  # Close grid
                all_cards_html += '</div>'  # Close scalability section

            # Related Keywords for SEO
            if offer.related_keywords and len(offer.related_keywords) > 0:
                all_cards_html += '<div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">'
                all_cards_html += '<span style="color: #64748b; font-size: 12px; font-weight: 600; margin-right: 4px;"><i class="bi bi-search"></i> SEO Keywords:</span>'

                for kw_data in offer.related_keywords[:5]:  # Show max 5 keywords
                    # Handle both dict format (new) and string format (old)
                    if isinstance(kw_data, dict):
                        keyword = kw_data.get("keyword", "")
                        volume = kw_data.get("volume", "")
                        safe_kw = html.escape(keyword)
                        safe_vol = html.escape(volume)
                        all_cards_html += f'<span style="background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 500;">{safe_kw} <span style="color: #94a3b8;">• {safe_vol}</span></span>'
                    else:
                        # Fallback for string format
                        safe_kw = html.escape(str(kw_data))
                        all_cards_html += f'<span style="background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 500;">{safe_kw}</span>'

                all_cards_html += '</div>'

            # Close card HTML
            if offer.tracking_url:
                all_cards_html += '</a>'  # Close anchor tag
            else:
                all_cards_html += '</div>'  # Close div

        all_cards_html += '</div>'

        # Render all cards in one block
        st.markdown(all_cards_html, unsafe_allow_html=True)

        # Export section with Bootstrap styling
        st.markdown('<div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e5e7eb;"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            <h3 style="color: #1e293b; font-weight: 700; margin-bottom: 8px;">
                <i class="bi bi-file-earmark-spreadsheet"></i> Export Results
            </h3>
            <p style="color: #64748b; font-size: 14px; margin-bottom: 20px;">
                Download your search results as a CSV file for further analysis
            </p>
            """, unsafe_allow_html=True)

        df_data = []
        for offer in offers:
            df_data.append({
                "Name": offer.name,
                "Advertiser": offer.advertiser_name,
                "Network": offer.network,
                "Commission Type": offer.commission_type,
                "Commission": offer.commission_value,
                "EPC": offer.epc,
                "Conv Rate": offer.conversion_rate,
                "YouTube Score": offer.youtube_score,
                "Scalability Score": offer.scalability_score,
                "Traffic": offer.traffic_monthly,
                "Cookie Duration": offer.cookie_duration,
                "Growth": offer.growth_percentage,
                "Competition": offer.competition_level,
                "Domain Authority": offer.domain_authority,
                "Instagram": offer.instagram_followers,
                "Category": offer.category,
                "Tracking URL": offer.tracking_url
            })

        df = pd.DataFrame(df_data)

        csv = df.to_csv(index=False).encode('utf-8')

        with col2:
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="affiliate_offers.csv",
                mime="text/csv",
                use_container_width=True
            )

    elif 'offers' in st.session_state:
        st.markdown("""
        <div class="alert alert-warning" role="alert" style="border-left: 4px solid #f59e0b; background-color: #fffbeb; border-radius: 8px; padding: 20px; text-align: center;">
            <i class="bi bi-exclamation-triangle" style="font-size: 24px; color: #f59e0b;"></i>
            <p style="margin-top: 12px; font-weight: 500; color: #92400e;">
                No offers found matching your criteria. Try adjusting the filters.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background-color: #f8fafc; border-radius: 12px; border: 2px dashed #cbd5e1;">
            <i class="bi bi-search" style="font-size: 64px; color: #cbd5e1;"></i>
            <h3 style="color: #475569; margin-top: 20px; font-weight: 600;">Ready to discover affiliate programs?</h3>
            <p style="color: #64748b; margin-top: 12px;">
                Enter your niche keyword and click "Search Offers" to get started
            </p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================================
    # TEMPORARY: Floating Chat Feedback Bubble (remove block when not needed)
    # =====================================================================
    if aggregator.sheets_cache:
        # Server-side: check for feedback in query params FIRST (before rendering)
        import urllib.parse
        params = st.query_params

        if params.get("fb_send"):
            fb_name = urllib.parse.unquote(params.get("fb_name", ""))
            fb_msg = urllib.parse.unquote(params.get("fb_msg", ""))
            if fb_msg.strip():
                try:
                    aggregator.sheets_cache.append_feedback(fb_name, fb_msg)
                    st.success("Feedback sent! Thank you.")
                except Exception as e:
                    st.error(f"Failed to send feedback: {e}")
            # Clear the query params so it doesn't re-submit on refresh
            st.query_params.clear()

        # Floating bubble injected via components.html (scripts execute here, unlike st.markdown)
        import streamlit.components.v1 as components
        _fb_user = html.escape(user_name or '')
        _fb_html = """
        <script>
        (function() {
            var doc = window.parent.document;

            // Only inject once
            if (doc.getElementById('fb-bubble')) return;

            // Inject styles into parent
            var style = doc.createElement('style');
            style.textContent = `
                #fb-bubble {
                    position: fixed;
                    bottom: 24px;
                    right: 24px;
                    z-index: 100000;
                    width: 56px;
                    height: 56px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    color: white;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    box-shadow: 0 4px 16px rgba(99,102,241,0.45);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                #fb-bubble:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 24px rgba(99,102,241,0.55);
                }
                #fb-popup {
                    display: none;
                    position: fixed;
                    bottom: 92px;
                    right: 24px;
                    z-index: 100000;
                    width: 340px;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 12px 40px rgba(0,0,0,0.2);
                    padding: 24px;
                    border: 1px solid #e5e7eb;
                }
                #fb-popup.open { display: block; }
                #fb-popup h3 {
                    margin: 0 0 16px;
                    font-size: 17px;
                    font-weight: 700;
                    color: #1e293b;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                }
                #fb-popup input, #fb-popup textarea {
                    width: 100%;
                    padding: 10px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    font-size: 14px;
                    font-family: inherit;
                    margin-bottom: 10px;
                    box-sizing: border-box;
                    outline: none;
                }
                #fb-popup input:focus, #fb-popup textarea:focus {
                    border-color: #6366f1;
                    box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
                }
                #fb-popup textarea { height: 80px; resize: vertical; }
                #fb-send-btn {
                    width: 100%;
                    padding: 11px;
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    font-family: inherit;
                }
                #fb-send-btn:hover { opacity: 0.9; }
                #fb-status { margin-top: 8px; font-size: 13px; text-align: center; }
            `;
            doc.head.appendChild(style);

            // Create bubble
            var bubble = doc.createElement('div');
            bubble.id = 'fb-bubble';
            bubble.textContent = String.fromCodePoint(0x1F4AC);
            doc.body.appendChild(bubble);

            // Create popup
            var popup = doc.createElement('div');
            popup.id = 'fb-popup';
            var fbUser = '__FB_USER__';
            var nameField = fbUser
                ? '<input type="text" id="fb-name" value="' + fbUser + '" readonly style="background:#f1f5f9;color:#475569;">'
                : '<input type="text" id="fb-name" placeholder="Your name" required>';
            popup.innerHTML = '<h3>Feedback</h3>'
                + nameField
                + '<textarea id="fb-msg" placeholder="What do you think? Any issues or suggestions?"></textarea>'
                + '<button id="fb-send-btn">Send Feedback</button>'
                + '<div id="fb-status"></div>';
            doc.body.appendChild(popup);

            // Toggle popup on bubble click
            bubble.addEventListener('click', function() {
                popup.classList.toggle('open');
            });

            // Submit feedback
            doc.getElementById('fb-send-btn').addEventListener('click', function() {
                var name = doc.getElementById('fb-name').value.trim();
                var msg = doc.getElementById('fb-msg').value.trim();
                var status = doc.getElementById('fb-status');
                if (!name) {
                    status.innerHTML = '<span style="color:#f59e0b;">Please enter your name</span>';
                    return;
                }
                if (!msg) {
                    status.innerHTML = '<span style="color:#f59e0b;">Please enter a message</span>';
                    return;
                }
                status.innerHTML = '<span style="color:#6366f1;">Sending...</span>';
                doc.getElementById('fb-name').value = '';
                doc.getElementById('fb-msg').value = '';
                var url = new URL(window.parent.location.href);
                url.searchParams.set('fb_name', encodeURIComponent(name));
                url.searchParams.set('fb_msg', encodeURIComponent(msg));
                url.searchParams.set('fb_send', '1');
                setTimeout(function() {
                    status.innerHTML = '<span style="color:#10b981;">&#10003; Sent! Thank you.</span>';
                    setTimeout(function() {
                        window.parent.location.href = url.toString();
                    }, 800);
                }, 200);
            });
        })();
        </script>
        """.replace('__FB_USER__', _fb_user)
        components.html(_fb_html, height=0)
    # =====================================================================
    # END: Floating Chat Feedback Bubble
    # =====================================================================

if __name__ == "__main__":
    main()
