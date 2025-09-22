import os
import requests
import json
import logging
import time
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from sqlalchemy.orm import Session
from .models import Destination, KnowledgeBase

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY environment variable is required")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        try:
            # Initialize OpenAI components with error handling
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.openai_api_key,
                request_timeout=30,
                max_retries=3
            )
            self.llm = OpenAI(
                openai_api_key=self.openai_api_key, 
                temperature=0.3,
                request_timeout=30,
                max_retries=3
            )
            self.chat_llm = ChatOpenAI(
                openai_api_key=self.openai_api_key, 
                temperature=0.3,
                request_timeout=30,
                max_retries=3
            )
            
            logger.info("OpenAI components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI components: {e}")
            raise
        
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Initialize geocoder for location lookup with error handling
        try:
            self.geocoder = Nominatim(
                user_agent="ai_travel_advisor",
                timeout=10
            )
            logger.info("Geocoder initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize geocoder: {e}")
            self.geocoder = None
        
        # Initialize weather tool
        self.weather_tool = Tool(
            name="get_weather",
            description="Get current weather for a destination. Only use when users specifically ask about weather or temperature.",
            func=self.get_weather_info_tool
        )
        
        # Create agent with error handling
        try:
            self.agent = self._create_agent()
            logger.info("AI agent created successfully")
        except Exception as e:
            logger.error(f"Failed to create AI agent: {e}")
            self.agent = None
    
    
    def _get_coordinates(self, destination_name: str) -> Optional[tuple]:
        """Get coordinates for a destination using geocoding with robust error handling"""
        if not self.geocoder:
            logger.warning("Geocoder not available")
            return None
            
        try:
            # Try exact match first
            location = self.geocoder.geocode(destination_name, exactly_one=True, timeout=10)
            if location:
                logger.info(f"Geocoded '{destination_name}' to: {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            
            # If no exact match, try with more context
            location = self.geocoder.geocode(f"{destination_name}, city", exactly_one=True, timeout=10)
            if location:
                logger.info(f"Geocoded '{destination_name}, city' to: {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
                
        except GeocoderTimedOut:
            logger.warning(f"Geocoding timeout for {destination_name}")
        except GeocoderServiceError as e:
            logger.warning(f"Geocoding service error for {destination_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error geocoding {destination_name}: {e}")
        
        return None
    
    def get_weather_info_tool(self, destination_name: str) -> str:
        """Tool function for getting weather info - used by LangChain agent"""
        weather_info = self.get_weather_info(destination_name)
        return weather_info if weather_info else f"Could not retrieve weather information for {destination_name}"
    
    def get_weather_info(self, destination_name: str) -> Optional[str]:
        """Get weather information for a destination using open-meteo API with robust error handling"""
        try:
            # Get coordinates for the destination
            coordinates = self._get_coordinates(destination_name)
            if not coordinates:
                logger.warning(f"Could not find coordinates for {destination_name}")
                return f"Could not find coordinates for {destination_name}"
            
            lat, lon = coordinates
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            
            # Make request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        weather_data = response.json()
                        current_weather = weather_data.get("current_weather", {})
                        
                        if current_weather:
                            temp = current_weather.get("temperature", "N/A")
                            weather_code = current_weather.get("weathercode", "N/A")
                            
                            # Simple weather code mapping
                            weather_descriptions = {
                                0: "Clear sky",
                                1: "Mainly clear",
                                2: "Partly cloudy",
                                3: "Overcast",
                                45: "Fog",
                                48: "Depositing rime fog",
                                51: "Light drizzle",
                                53: "Moderate drizzle",
                                55: "Dense drizzle",
                                61: "Slight rain",
                                63: "Moderate rain",
                                65: "Heavy rain",
                                71: "Slight snow",
                                73: "Moderate snow",
                                75: "Heavy snow",
                                80: "Slight rain showers",
                                81: "Moderate rain showers",
                                82: "Violent rain showers",
                                95: "Thunderstorm",
                                96: "Thunderstorm with slight hail",
                                99: "Thunderstorm with heavy hail"
                            }
                            
                            weather_desc = weather_descriptions.get(weather_code, f"Weather code: {weather_code}")
                            logger.info(f"Retrieved weather for {destination_name}: {weather_desc}, {temp}°C")
                            return f"Current weather in {destination_name}: {weather_desc}, Temperature: {temp}°C"
                        else:
                            logger.warning(f"No current weather data available for {destination_name}")
                            return f"No current weather data available for {destination_name}"
                    else:
                        logger.warning(f"Weather API returned status {response.status_code} for {destination_name}")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Wait before retry
                            continue
                        return f"Weather service temporarily unavailable for {destination_name}"
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Weather API timeout for {destination_name} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return f"Weather service timeout for {destination_name}"
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Weather API request error for {destination_name}: {e} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return f"Weather service error for {destination_name}"
            
        except Exception as e:
            logger.error(f"Unexpected error fetching weather for {destination_name}: {e}")
        
        return None
    
    def _create_agent(self) -> Optional[AgentExecutor]:
        """Create LangChain agent with weather tool and error handling"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a concise AI travel advisor. Answer questions about destinations using the provided context. Only use the weather tool if users specifically ask about weather or temperature. Keep responses focused and relevant to the question asked."""),
                ("user", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            agent = create_openai_tools_agent(
                llm=self.chat_llm,
                tools=[self.weather_tool],
                prompt=prompt
            )
            
            return AgentExecutor(
                agent=agent, 
                tools=[self.weather_tool], 
                verbose=False,
                max_iterations=3,
                return_intermediate_steps=False
            )
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
    
    def build_vector_store(self, db: Session, destination_id: int) -> bool:
        """Build or update vector store for a specific destination with error handling"""
        try:
            # Get all knowledge base entries for this destination
            knowledge_entries = db.query(KnowledgeBase).filter(
                KnowledgeBase.destination_id == destination_id
            ).all()
            
            if not knowledge_entries:
                logger.info(f"No knowledge entries found for destination {destination_id}")
                return False
            
            # Create documents
            documents = []
            for entry in knowledge_entries:
                doc = Document(
                    page_content=entry.content,
                    metadata={"id": entry.id, "destination_id": entry.destination_id}
                )
                documents.append(doc)
            
            # Split documents into chunks
            texts = self.text_splitter.split_documents(documents)
            
            if texts:
                # Create vector store with error handling
                try:
                    self.vector_store = FAISS.from_documents(texts, self.embeddings)
                    logger.info(f"Vector store built successfully for destination {destination_id} with {len(texts)} chunks")
                    return True
                except Exception as e:
                    logger.error(f"Failed to create vector store: {e}")
                    return False
            
            logger.warning(f"No text chunks created for destination {destination_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error building vector store for destination {destination_id}: {e}")
            return False
    
    def get_relevant_context(self, question: str, top_k: int = 2) -> str:
        """Retrieve relevant context from vector store with error handling"""
        if not self.vector_store:
            return ""
        
        try:
            # Search for relevant documents
            docs = self.vector_store.similarity_search(question, k=top_k)
            
            if not docs:
                return ""
            
            # Combine the content with minimal formatting
            context = "\n".join([doc.page_content for doc in docs])
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    def generate_answer(self, question: str, context: str, weather_info: Optional[str] = None) -> str:
        """Generate answer using LLM with context and weather info with error handling"""
        try:
            # Build concise prompt
            prompt_parts = []
            
            if context:
                prompt_parts.append(f"Context: {context}")
            
            if weather_info:
                prompt_parts.append(f"Weather: {weather_info}")
            
            prompt_parts.append(f"Question: {question}")
            prompt_parts.append("Provide a concise, helpful answer based on the available information.")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            try:
                response = self.llm(full_prompt)
                return response.strip()
            except Exception as llm_error:
                logger.error(f"LLM generation error: {llm_error}")
                if context:
                    return f"Based on available information: {context[:200]}..."
                else:
                    return "I'm experiencing technical difficulties. Please try again later."
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "I encountered an error. Please try again."
    
    def process_query(self, db: Session, destination_id: int, question: str) -> dict:
        """Process a complete AI query using LangChain agent with error handling"""
        try:
            # Get destination name
            destination = db.query(Destination).filter(Destination.id == destination_id).first()
            if not destination:
                return {"answer": "Destination not found.", "weather_info": None}
            
            # Build vector store and get context
            self.build_vector_store(db, destination_id)
            context = self.get_relevant_context(question)
            
            # Prepare input for agent with context
            agent_input = f"Destination: {destination.name}\nContext: {context}\nQuestion: {question}"
            
            # Use agent to process the query if available
            if self.agent:
                try:
                    result = self.agent.invoke({"input": agent_input})
                    answer = result.get("output", "I couldn't process your request.")
                except Exception as agent_error:
                    logger.error(f"Agent error: {agent_error}")
                    answer = self.generate_answer(question, context, None)
            else:
                answer = self.generate_answer(question, context, None)
            
            return {
                "answer": answer,
                "weather_info": None  # Weather is integrated into the answer
            }
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "answer": "I encountered an error. Please try again later.",
                "weather_info": None
            }

# Global AI service instance
ai_service = AIService()
