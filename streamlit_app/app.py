import streamlit as st
import asyncio
import requests
import tempfile
import os
import time
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from orchestrator.main_orchestrator import MainOrchestrator, OrchestratorRequest

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    return MainOrchestrator()

orchestrator = get_orchestrator()

# Main UI
st.title("🤖 Multi-Agent Finance Assistant")
st.markdown("*Your AI-powered financial market briefing system*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Mode selection
    mode = st.selectbox(
        "Interaction Mode",
        ["Text", "Voice"],
        help="Choose between text-based or voice-based interaction"
    )
    
    # Agent status
    st.header("🔧 Agent Status")
    agent_ports = {
        "API Agent": 8001,
        "Retriever Agent": 8003,
        "Language Agent": 8005,
        "Voice Agent": 8006
    }
    
    for agent_name, port in agent_ports.items():
        try:
            response = requests.get(f"http://localhost:{port}/docs", timeout=10)
            if response.status_code == 200:
                st.success(f"✅ {agent_name}")
            else:
                st.error(f"❌ {agent_name}")
        except:
            st.error(f"❌ {agent_name}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat Interface")
    
    if mode == "Text":
        # Text input
        user_query = st.text_input(
            "Enter your financial query:",
            placeholder="What's our risk exposure in Asia tech stocks today?"
        )
        
        submit_button = st.button("Submit Query", type="primary")
        
        if submit_button and user_query:
            with st.spinner("Processing your request..."):
                try:
                    # Create orchestrator request
                    request = OrchestratorRequest(query=user_query, mode="text")
                    
                    # Process request (simulate async)
                    response = asyncio.run(orchestrator.process_request(request))
                    
                    # Display response
                    st.success("Response generated successfully!")
                    st.markdown("### 📊 Financial Brief")
                    st.write(response.response)
                    
                    # Show confidence
                    confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                    st.markdown(f"**Confidence:** :{confidence_color}[{response.confidence:.2%}]")
                    
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
    
    else:  # Voice mode
        st.markdown("### 🎤 Voice Interface")
        
        # Audio input
        audio_file = st.file_uploader("Upload audio file", type=['wav', 'mp3', 'ogg'])
        
        if audio_file is not None:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            
            st.audio(audio_file)
            
            if st.button("Process Voice Query", type="primary"):
                with st.spinner("Processing voice input..."):
                    try:
                        # Create orchestrator request
                        request = OrchestratorRequest(
                            query="", 
                            mode="voice", 
                            audio_file=tmp_file_path
                        )
                        
                        # Process request
                        response = asyncio.run(orchestrator.process_request(request))
                        
                        # Display response
                        st.success("Voice response generated!")
                        st.markdown("### 📊 Financial Brief")
                        st.write(response.response)
                        
                        # Play audio response if available
                        if response.audio_file:
                            st.audio(response.audio_file)
                        
                        # Show confidence
                        confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                        st.markdown(f"**Confidence:** :{confidence_color}[{response.confidence:.2%}]")
                        
                        # Cleanup
                        os.unlink(tmp_file_path)
                        
                    except Exception as e:
                        st.error(f"Error processing voice input: {str(e)}")
                        os.unlink(tmp_file_path)

with col2:
    st.header("📈 Market Overview")
    
    # Sample market data display
    try:
        market_response = requests.get("http://localhost:8001/asia_tech_stocks", timeout=5)
        if market_response.status_code == 200:
            market_data = market_response.json()["data"]
            
            for stock in market_data[:5]:  # Show top 5
                symbol = stock.get("symbol", "N/A")
                price = stock.get("current_price", 0)
                change = stock.get("change_percent", 0)
                
                # Color code based on change
                color = "green" if change >= 0 else "red"
                arrow = "↗" if change >= 0 else "↘"
                
                st.markdown(f"""
                **{symbol}**  
                ${price:.2f} :{color}[{arrow} {change:.2f}%]
                """)
        else:
            st.warning("Market data unavailable")
            
    except Exception as e:
        st.warning("Unable to fetch market data")
    
    # Quick action buttons
    st.header("🚀 Quick Actions")
    
    sample_queries = [
        "What's our Asia tech exposure?",
        "Show me earnings surprises",
        "Market sentiment analysis",
        "Risk assessment today"
    ]
    
    for query in sample_queries:
        if st.button(query, key=f"quick_{query}"):
            try:
                request = OrchestratorRequest(query=query, mode="text")
                response = asyncio.run(orchestrator.process_request(request))
                
                st.markdown("### Quick Response")
                st.write(response.response)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, FastAPI, Ollama, and multiple AI agents")