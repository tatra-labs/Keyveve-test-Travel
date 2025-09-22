import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

# Page configuration
st.set_page_config(
    page_title="AI Travel Advisor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .page-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .destination-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    .note-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
    }
    .ai-response {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin-top: 1rem;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        word-wrap: break-word;
    }
    .ai-message {
        background-color: #e9ecef;
        color: #333;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        word-wrap: break-word;
    }
    .message-time {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.25rem;
    }
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background-color: white;
        padding: 1rem 0;
        border-top: 1px solid #ddd;
    }
    .weather-info {
        background-color: #e2e3e5;
        padding: 0.5rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-style: italic;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

class APIService:
    """Service class to handle API communication"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_destinations(self) -> List[Dict]:
        """Get all destinations"""
        try:
            response = requests.get(f"{self.base_url}/destinations")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching destinations: {str(e)}")
            return []
    
    def create_destination(self, name: str) -> Optional[Dict]:
        """Create a new destination"""
        try:
            response = requests.post(
                f"{self.base_url}/destinations",
                json={"name": name}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error creating destination: {str(e)}")
            return None
    
    def delete_destination(self, destination_id: int) -> bool:
        """Delete a destination"""
        try:
            response = requests.delete(f"{self.base_url}/destinations/{destination_id}")
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Error deleting destination: {str(e)}")
            return False
    
    def get_notes(self, destination_id: int) -> List[Dict]:
        """Get notes for a destination"""
        try:
            response = requests.get(f"{self.base_url}/destinations/{destination_id}/notes")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching notes: {str(e)}")
            return []
    
    def create_note(self, destination_id: int, content: str) -> Optional[Dict]:
        """Create a new note"""
        try:
            response = requests.post(
                f"{self.base_url}/destinations/{destination_id}/notes",
                json={"content": content}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error creating note: {str(e)}")
            return None
    
    def ask_ai(self, destination_id: int, question: str) -> Optional[Dict]:
        """Ask AI a question about a destination"""
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json={"destination_id": destination_id, "question": question}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error asking AI: {str(e)}")
            return None

# Initialize API service
api_service = APIService(API_BASE_URL)

def initialize_chat_history():
    """Initialize chat history in session state"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}
    if 'pending_question' not in st.session_state:
        st.session_state.pending_question = None
    if 'processing_response' not in st.session_state:
        st.session_state.processing_response = False

def add_message_to_history(destination_id: int, message: str, is_user: bool = True, weather_info: str = None):
    """Add a message to chat history"""
    if destination_id not in st.session_state.chat_history:
        st.session_state.chat_history[destination_id] = []
    
    message_data = {
        'message': message,
        'is_user': is_user,
        'timestamp': datetime.now().strftime('%H:%M'),
        'weather_info': weather_info
    }
    st.session_state.chat_history[destination_id].append(message_data)

def get_chat_history(destination_id: int):
    """Get chat history for a destination"""
    return st.session_state.chat_history.get(destination_id, [])

def clear_chat_history(destination_id: int):
    """Clear chat history for a destination"""
    if destination_id in st.session_state.chat_history:
        st.session_state.chat_history[destination_id] = []

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">✈️ AI Travel Advisor</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Destinations", "📚 Knowledge Base", "✨ Ask AI"]
    )
    
    # Display selected page
    if page == "🏠 Destinations":
        destinations_page()
    elif page == "📚 Knowledge Base":
        knowledge_base_page()
    elif page == "✨ Ask AI":
        qa_page()

def destinations_page():
    """Destinations management page"""
    st.markdown('<h2 class="page-header">🏠 Destinations</h2>', unsafe_allow_html=True)
    
    st.subheader("Add New Destination")
    # Add new destination
    with st.form("add_destination"):
        col1, col2 = st.columns([3, 1])
        with col1:
            destination_name = st.text_input("Destination Name", placeholder="e.g., Type Destination Name Here (e.g., Paris, Tokyo, New York)", label_visibility="collapsed")
        with col2:
            add_button = st.form_submit_button("Add Destination", use_container_width=True)
        
        if add_button and destination_name:
            if api_service.create_destination(destination_name.strip()):
                st.success(f"✅ Added destination: {destination_name}")
                st.rerun()
    
    # Display existing destinations
    st.subheader("Your Destinations")
    destinations = api_service.get_destinations()
    
    if not destinations:
        st.info("No destinations yet. Add your first destination above!")
        return
    
    for destination in destinations:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="destination-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{destination['name']}</strong><br>
                            <small>Added: {datetime.fromisoformat(destination['created_at'].replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("❌", key=f"delete_{destination['id']}", help="Delete destination"):
                    if api_service.delete_destination(destination['id']):
                        st.success("Destination deleted!")
                        st.rerun()

def knowledge_base_page():
    """Knowledge base page"""
    st.markdown('<h2 class="page-header">📚 Knowledge Base</h2>', unsafe_allow_html=True)
    
    # Get destinations for selection
    destinations = api_service.get_destinations()
    
    if not destinations:
        st.warning("No destinations available. Please add destinations first!")
        return
    
    st.subheader("Select Destination")
    # Destination selection
    destination_options = {f"{d['name']}": d['id'] for d in destinations}
    selected_destination = st.selectbox("Select Destination", list(destination_options.keys()), label_visibility="collapsed")
    destination_id = destination_options[selected_destination]
    
    # Add new note
    st.subheader("Add New Note")
    with st.form("add_note"):
        note_content = st.text_area("Note Content", placeholder="Enter your notes about this destination...", height=150)
        add_note_button = st.form_submit_button("Add Note")
        
        if add_note_button and note_content.strip():
            if api_service.create_note(destination_id, note_content.strip()):
                st.success("✅ Note added successfully!")
                st.rerun()
    
    # Display existing notes
    st.subheader("Existing Notes")
    notes = api_service.get_notes(destination_id)
    
    if not notes:
        st.info("No notes for this destination yet. Add your first note above!")
        return
    
    for note in notes:
        st.markdown(f"""
        <div class="note-card">
            <strong>Note #{note['id']}</strong><br>
            <small>Added: {datetime.fromisoformat(note['created_at'].replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}</small><br><br>
            {note['content']}
        </div>
        """, unsafe_allow_html=True)

def qa_page():
    """Chat-style Q&A page"""
    st.markdown('<h2 class="page-header">✨ Ask AI</h2>', unsafe_allow_html=True)
    
    # Initialize chat history
    initialize_chat_history()
    
    # Get destinations for selection
    destinations = api_service.get_destinations()
    
    if not destinations:
        st.warning("No destinations available. Please add destinations first!")
        return
    
    # Destination selection
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Select Destination")
        destination_options = {f"{d['name']}": d['id'] for d in destinations}
        selected_destination = st.selectbox("Select Destination", list(destination_options.keys()), label_visibility="collapsed")
        destination_id = destination_options[selected_destination]
    
    with col2:
        st.subheader("Actions")
        if st.button("🗑️ Clear Chat", help="Clear chat history for this destination"):
            clear_chat_history(destination_id)
            st.rerun()
    
    # Chat history display
    st.subheader("Chat with AI Travel Advisor")
    chat_history = get_chat_history(destination_id)
    
    if not chat_history and not st.session_state.pending_question:
        st.markdown('<div style="text-align: center; color: #666; margin: 4rem;">Start a conversation by asking a question below!</div>', unsafe_allow_html=True)
    else:
        # Display chat history
        for msg in chat_history:
            if msg['is_user']:
                st.markdown(f'''
                <div class="user-message">
                    {msg['message']}
                    <div class="message-time">You • {msg['timestamp']}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="ai-message">
                    {msg['message']}
                    <div class="message-time">AI • {msg['timestamp']}</div>
                </div>
                ''', unsafe_allow_html=True)
                if msg.get('weather_info'):
                    st.markdown(f'''
                    <div class="weather-info" style="margin-right: 20%;">
                        <strong>🌤️ Weather Information:</strong><br>
                        {msg['weather_info']}
                    </div>
                    ''', unsafe_allow_html=True)
        
        # Display pending question if any
        if st.session_state.pending_question:
            st.markdown(f'''
            <div class="user-message">
                {st.session_state.pending_question}
                <div class="message-time">You • {datetime.now().strftime('%H:%M')}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Show processing indicator
            if st.session_state.processing_response:
                st.markdown(f'''
                <div class="ai-message">
                    <em>✨ AI is thinking...</em>
                    <div class="message-time">AI • {datetime.now().strftime('%H:%M')}</div>
                </div>
                ''', unsafe_allow_html=True)
    
    with st.form("ask_question", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            question = st.text_input("Your Question", placeholder="e.g., What's the best museum to visit and how's the weather?", label_visibility="collapsed")
        with col2:
            ask_button = st.form_submit_button("Ask AI", use_container_width=True)
        
        if ask_button and question.strip():
            # Set pending question and processing state
            st.session_state.pending_question = question.strip()
            st.session_state.processing_response = True
            st.rerun()
    
    # Process pending question if exists
    if st.session_state.pending_question and st.session_state.processing_response:
        # Add user message to history
        add_message_to_history(destination_id, st.session_state.pending_question, is_user=True)
        
        # Get AI response
        response = api_service.ask_ai(destination_id, st.session_state.pending_question)
        
        if response:
            # Add AI response to history
            add_message_to_history(
                destination_id, 
                response['answer'], 
                is_user=False, 
                weather_info=response.get('weather_info')
            )
        
        # Clear pending states
        st.session_state.pending_question = None
        st.session_state.processing_response = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
