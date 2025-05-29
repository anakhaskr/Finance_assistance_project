import streamlit as st
import asyncio
import requests
import tempfile
import os
import time
import sys



sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from orchestrator.main_orchestrator import MainOrchestrator, OrchestratorRequest


st.set_page_config(
    page_title="Multi-Agent Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_orchestrator():
    return MainOrchestrator()

orchestrator = get_orchestrator()


st.title("🤖 Multi-Agent Finance Assistant")
st.markdown("*Your AI-powered financial market briefing system with real-time news and data*")


with st.sidebar:
    st.header("⚙️ Configuration")
    

    mode = st.selectbox(
        "Interaction Mode",
        ["Text", "Voice"],
        help="Choose between text-based or voice-based interaction"
    )
    
   
    st.header("🔧 Agent Status")
    agent_ports = {
        "API Agent": 8001,
        "Scraping Agent": 8002,
        "Retriever Agent": 8003,
        "Analysis Agent": 8004,
        "Language Agent": 8005,
        "Voice Agent": 8006
    }
    
    for agent_name, port in agent_ports.items():
        try:
            response = requests.get(f"http://localhost:{port}/docs", timeout=2)
            if response.status_code == 200:
                st.success(f"✅ {agent_name}")
            else:
                st.error(f"❌ {agent_name}")
        except:
            st.error(f"❌ {agent_name}")
    

    st.header("🔄 Data Sources")
    if st.button("Refresh News Data"):
        try:
            news_response = requests.get("http://localhost:8002/scrape_news", timeout=10)
            if news_response.status_code == 200:
                st.success("✅ News data refreshed")
            else:
                st.error("❌ Failed to refresh news")
        except:
            st.error("❌ News scraping agent unavailable")
    
    if st.button("Refresh Earnings Data"):
        try:
            earnings_response = requests.get("http://localhost:8002/scrape_earnings", timeout=10)
            if earnings_response.status_code == 200:
                st.success("✅ Earnings data refreshed")
            else:
                st.error("❌ Failed to refresh earnings")
        except:
            st.error("❌ Scraping agent unavailable")


col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat Interface")
    
    if mode == "Text":
      
        user_query = st.text_input(
            "Enter your financial query:",
            placeholder="What's the latest news on Asia tech stocks today?"
        )
        
        submit_button = st.button("Submit Query", type="primary")
        
        if submit_button and user_query:
            with st.spinner("Processing your request..."):
                try:
                  
                    request = OrchestratorRequest(query=user_query, mode="text")
                    
               
                    response = asyncio.run(orchestrator.process_request(request))
                    
                   
                    st.success("Response generated successfully!")
                    st.markdown("### 📊 Financial Brief")
                    st.write(response.response)
                    
                    
                    confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                    st.markdown(f"**Confidence:** :{confidence_color}[{response.confidence:.2%}]")
                    
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
    
    else:  
        st.markdown("### 🎤 Voice Interface")
        
       
        audio_file = st.file_uploader("Upload audio file", type=['wav', 'mp3', 'ogg'])
        
        if audio_file is not None:
          
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            
            st.audio(audio_file)
            
            if st.button("Process Voice Query", type="primary"):
                with st.spinner("Processing voice input..."):
                    try:
                       
                        request = OrchestratorRequest(
                            query="", 
                            mode="voice", 
                            audio_file=tmp_file_path
                        )
                        
                    
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
    
    # Market data display
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
    
    # Latest News Section
    st.header("📰 Latest News")
    try:
        news_response = requests.get("http://localhost:8002/scrape_news", timeout=10)
        if news_response.status_code == 200:
            news_data = news_response.json()["data"]
            
            for news in news_data[:3]:  # Show top 3 news
                title = news.get("title", "No title")
                source = news.get("source", "Unknown")
                link = news.get("link", "#")
                
                st.markdown(f"""
                **{title[:60]}{'...' if len(title) > 60 else ''}**  
                *Source: {source}*
                """)
                
                if link != "#":
                    st.markdown(f"[Read more]({link})")
                st.markdown("---")
        else:
            st.warning("Unable to fetch latest news")
    except Exception as e:
        st.warning("News scraping unavailable")
    
    # Earnings Calendar Section
    st.header("📅 Earnings Calendar")
    try:
        earnings_response = requests.get("http://localhost:8002/scrape_earnings", timeout=10)
        if earnings_response.status_code == 200:
            earnings_data = earnings_response.json()["data"]
            
            for earnings in earnings_data[:3]:  # Show top 3 earnings
                company = earnings.get("company", "Unknown")
                symbol = earnings.get("symbol", "N/A")
                date = earnings.get("date", "TBD")
                estimate = earnings.get("estimate", 0)
                actual = earnings.get("actual", "N/A")
                
                # Color code based on beat/miss
                if actual != "N/A" and estimate:
                    beat_miss = "🟢 Beat" if actual > estimate else "🔴 Miss"
                else:
                    beat_miss = "⏳ Pending"
                
                st.markdown(f"""
                **{company} ({symbol})**  
                Date: {date}  
                Est: ${estimate:.2f} | Act: ${actual if actual != 'N/A' else 'TBD'}  
                {beat_miss}
                """)
                st.markdown("---")
        else:
            st.warning("Unable to fetch earnings data")
    except Exception as e:
        st.warning("Earnings data unavailable")
    
    # Quick action buttons
    st.header("🚀 Quick Actions")
    
    sample_queries = [
        "What's our Asia tech exposure?",
        "Show me latest financial news",
        "Any earnings surprises today?",
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
                
                # Show confidence
                confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                st.markdown(f"**Confidence:** :{confidence_color}[{response.confidence:.2%}]")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Additional tabs for detailed views
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Data Sources", "🔍 System Logs", "ℹ️ About"])

with tab1:
    st.header("Data Source Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Market Data APIs")
        try:
            api_status = requests.get("http://localhost:8001/asia_tech_stocks", timeout=5)
            if api_status.status_code == 200:
                st.success("✅ Yahoo Finance API Active")
                data_count = len(api_status.json().get("data", []))
                st.metric("Active Stocks", data_count)
            else:
                st.error("❌ Market Data API Down")
        except:
            st.error("❌ API Agent Unavailable")
    
    with col2:
        st.subheader("News Scraping")
        try:
            news_status = requests.get("http://localhost:8002/scrape_news", timeout=10)
            if news_status.status_code == 200:
                st.success("✅ News Scraping Active")
                news_count = len(news_status.json().get("data", []))
                st.metric("Latest Articles", news_count)
            else:
                st.error("❌ News Scraping Failed")
        except:
            st.error("❌ Scraping Agent Down")
    
    with col3:
        st.subheader("Vector Store")
        try:
            retriever_status = requests.post(
                "http://localhost:8003/search", 
                json={"query": "test", "top_k": 1},
                timeout=5
            )
            if retriever_status.status_code == 200:
                st.success("✅ Vector Store Active")
                st.metric("Embeddings", "Ready")
            else:
                st.error("❌ Vector Store Error")
        except:
            st.error("❌ Retriever Agent Down")

with tab2:
    st.header("System Performance")
    
    # Agent response times
    st.subheader("Agent Response Times")
    
    agent_times = {}
    for agent_name, port in agent_ports.items():
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:{port}/docs", timeout=2)
            end_time = time.time()
            
            if response.status_code == 200:
                agent_times[agent_name] = round((end_time - start_time) * 1000, 2)
            else:
                agent_times[agent_name] = "Error"
        except:
            agent_times[agent_name] = "Timeout"
    
    for agent, time_ms in agent_times.items():
        if isinstance(time_ms, float):
            color = "green" if time_ms < 500 else "orange" if time_ms < 1000 else "red"
            st.markdown(f"**{agent}**: :{color}[{time_ms}ms]")
        else:
            st.markdown(f"**{agent}**: :red[{time_ms}]")

with tab3:
    st.header("About This System")
    
    st.markdown("""
    ### 🤖 Multi-Agent Finance Assistant
    
    This system uses 6 specialized AI agents to provide comprehensive financial market analysis:
    
    - **API Agent** (8001): Real-time market data from Yahoo Finance
    - **Scraping Agent** (8002): Latest financial news and earnings data
    - **Retriever Agent** (8003): Document search using FAISS vector store
    - **Analysis Agent** (8004): Financial calculations and risk analysis
    - **Language Agent** (8005): Response synthesis using Ollama LLM
    - **Voice Agent** (8006): Speech-to-text and text-to-speech processing
    
    ### 🛠️ Technology Stack
    - **Backend**: FastAPI microservices
    - **LLM**: Ollama (Llama2/Mistral)
    - **Vector Store**: FAISS with Sentence Transformers
    - **Frontend**: Streamlit
    - **Voice**: SpeechRecognition + pyttsx3
    - **Data**: Yahoo Finance API + Web Scraping
    
    ### 📊 Capabilities
    - Real-time market data analysis
    - Voice-enabled queries and responses
    - Financial news aggregation
    - Earnings calendar tracking
    - Risk exposure calculations
    - Portfolio insights and recommendations
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, FastAPI, Ollama, and multiple AI agents | Powered by real-time financial data")
