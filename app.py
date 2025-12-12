import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os

# Check if running locally or on Hugging Face
if os.getenv("SPACE_ID"):
    # Running on Hugging Face - use internal API
    API_URL = "http://127.0.0.1:7860"
else:
    # Running locally
    API_URL = "http://localhost:8000"


# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 AI Agent Dashboard")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Overview", "💬 Chat", "📅 Appointments", "👥 Users", "📜 History"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown(f"[API Docs]({API_URL}/docs)")
    st.markdown(f"[Health Check]({API_URL}/health)")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info("Multi-Channel AI Agent with WhatsApp integration, persistent memory, and appointment booking.")

# Fetch stats
@st.cache_data(ttl=5)
def get_stats():
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        return response.json()
    except:
        return None

@st.cache_data(ttl=5)
def get_appointments():
    try:
        response = requests.get(f"{API_URL}/appointments", timeout=5)
        return response.json()
    except:
        return None

# PAGE 1: Overview
if page == "📊 Overview":
    st.title("📊 Dashboard Overview")
    
    stats = get_stats()
    
    if stats:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Users", stats['total_users'])
        
        with col2:
            st.metric("💬 Total Conversations", stats['total_conversations'])
        
        with col3:
            st.metric("📅 Total Appointments", stats['total_appointments'])
        
        with col4:
            whatsapp = stats['channels'].get('whatsapp', 0)
            st.metric("📱 WhatsApp Messages", whatsapp)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Channel Distribution
            st.subheader("📱 Channel Distribution")
            whatsapp_count = stats['channels'].get('whatsapp', 0)
            web_count = stats['channels'].get('web', 0)
            
            if whatsapp_count > 0 or web_count > 0:
                channel_data = pd.DataFrame({
                    'Channel': ['WhatsApp', 'Web'],
                    'Count': [whatsapp_count, web_count]
                })
                fig = px.pie(
                    channel_data, 
                    values='Count', 
                    names='Channel',
                    color='Channel',
                    color_discrete_map={'WhatsApp': '#25D366', 'Web': '#0088cc'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No conversations yet. Start chatting to see data!")
        
        with col2:
            # Recent Activity
            st.subheader("📈 Activity Timeline")
            if stats['recent_conversations']:
                recent_df = pd.DataFrame(stats['recent_conversations'])
                recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'])
                recent_df['hour'] = recent_df['timestamp'].dt.hour
                
                activity = recent_df.groupby('hour').size().reset_index(name='count')
                
                fig = px.bar(
                    activity, 
                    x='hour', 
                    y='count',
                    labels={'hour': 'Hour of Day', 'count': 'Messages'},
                    title="Messages by Hour"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No activity data yet")
        
        # Recent Conversations Table
        st.markdown("---")
        st.subheader("💬 Recent Conversations")
        
        if stats['recent_conversations']:
            conv_df = pd.DataFrame(stats['recent_conversations'])
            conv_df['timestamp'] = pd.to_datetime(conv_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            display_df = conv_df[['name', 'phone', 'channel', 'message', 'timestamp']].copy()
            display_df.columns = ['Name', 'Phone', 'Channel', 'Message', 'Time']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("💬 No conversations yet. Start chatting to see data here!")
        
        # Recent Appointments
        if stats['recent_appointments']:
            st.markdown("---")
            st.subheader("📅 Recent Appointments")
            
            appt_df = pd.DataFrame(stats['recent_appointments'])
            st.dataframe(
                appt_df,
                use_container_width=True,
                hide_index=True
            )
    
    else:
        st.error("❌ Could not connect to API. Make sure the server is running on port 8000.")
        st.code("uvicorn app.main:app --reload --port 8000")

# PAGE 2: Chat Interface
elif page == "💬 Chat":
    st.title("💬 Chat with AI Agent")
    
    # Session state for chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"web-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            role = message['role']
            content = message['content']
            
            if role == 'user':
                st.markdown(f'<div class="chat-message user-message">👤 <strong>You:</strong> {content}</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message">🤖 <strong>Agent:</strong> {content}</div>', 
                          unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message", 
                placeholder="Type your message here... (e.g., 'Book appointment tomorrow at 3pm')",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("Send 📤", use_container_width=True)
    
    if submit and user_input:
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get bot response
        try:
            with st.spinner("🤖 Agent is thinking..."):
                response = requests.post(
                    f"{API_URL}/chat/web",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "user_name": "Dashboard User"
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                bot_response = response.json()['response']
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': bot_response
                })
            else:
                st.error("❌ Failed to get response from agent")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        
        st.rerun()
    
    # Sidebar options
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 Chat Options")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = f"web-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.rerun()
        
        st.info(f"Session ID: `{st.session_state.session_id}`")
        st.caption(f"Messages: {len(st.session_state.messages)}")

# PAGE 3: Appointments
elif page == "📅 Appointments":
    st.title("📅 Appointments Manager")
    
    appointments_data = get_appointments()
    
    if appointments_data and appointments_data['total'] > 0:
        appointments = appointments_data['appointments']
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "scheduled", "completed", "cancelled"]
            )
        
        with col2:
            st.metric("Total Appointments", appointments_data['total'])
        
        # Convert to DataFrame
        df = pd.DataFrame(appointments)
        
        # Apply filter
        if status_filter != "All":
            df = df[df['status'] == status_filter]
        
        # Display metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Filtered Results", len(df))
        with col2:
            scheduled = len(df[df['status'] == 'scheduled'])
            st.metric("📅 Scheduled", scheduled)
        with col3:
            with_email = len(df[df['email'].notna()])
            st.metric("📧 With Email", with_email)
        with col4:
            reminders = len(df[df['reminder_sent'] == True])
            st.metric("✅ Reminders Sent", reminders)
        
        st.markdown("---")
        
        # Display table
        st.subheader("📋 Appointments List")
        display_df = df[['customer_name', 'phone', 'email', 'date', 'time', 'status', 'reminder_sent']].copy()
        display_df.columns = ['Customer', 'Phone', 'Email', 'Date', 'Time', 'Status', 'Reminder Sent']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"appointments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    else:
        st.info("📅 No appointments yet. Book an appointment via WhatsApp or chat to see them here!")
        
        with st.expander("💡 How to book an appointment"):
            st.markdown("""
            **Via Chat:**
            - "Book appointment tomorrow at 3pm"
            - "Schedule for 2025-12-20 at 14:30"
            
            **Via WhatsApp:**
            - Send same messages to your WhatsApp number
            - Make sure to include your email for confirmation
            """)

# PAGE 4: Users
elif page == "👥 Users":
    st.title("👥 Users Management")
    
    stats = get_stats()
    
    if stats and stats['total_users'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("👥 Total Users", stats['total_users'])
        
        with col2:
            st.metric("💬 Total Messages", stats['total_conversations'])
        
        st.markdown("---")
        
        # Recent Active Users
        if stats['recent_conversations']:
            st.subheader("👥 Recent Active Users")
            
            # Group by user
            users_data = {}
            for conv in stats['recent_conversations']:
                phone = conv['phone']
                if phone not in users_data:
                    users_data[phone] = {
                        'Name': conv['name'] or 'Unknown',
                        'Phone': phone,
                        'Channel': conv['channel'],
                        'Last Active': conv['timestamp'],
                        'Messages': 1
                    }
                else:
                    users_data[phone]['Messages'] += 1
            
            users_df = pd.DataFrame(list(users_data.values()))
            users_df['Last Active'] = pd.to_datetime(users_df['Last Active']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(users_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("👥 No users yet. Start a conversation to see users here!")

# PAGE 5: Conversation History
elif page == "📜 History":
    st.title("📜 Conversation History")
    
    stats = get_stats()
    
    if stats and stats['recent_conversations']:
        st.subheader(f"Recent Conversations ({len(stats['recent_conversations'])})")
        
        for i, conv in enumerate(stats['recent_conversations']):
            with st.expander(f"💬 {conv['name']} ({conv['channel']}) - {conv['timestamp'][:16]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**👤 Name:** {conv['name']}")
                    st.markdown(f"**📱 Phone:** {conv['phone']}")
                
                with col2:
                    st.markdown(f"**📡 Channel:** {conv['channel']}")
                    st.markdown(f"**🕐 Time:** {conv['timestamp']}")
                
                st.markdown("---")
                st.markdown(f"**💬 Message:**")
                st.info(conv['message'])
    
    else:
        st.info("📜 No conversation history yet. Start chatting to see history here!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "🤖 Multi-Channel AI Agent Dashboard | "
    f"<a href='{API_URL}/docs' target='_blank'>API Docs</a> | "
    f"<a href='{API_URL}/health' target='_blank'>Health Check</a>"
    "</div>",
    unsafe_allow_html=True
)
