# AI Travel Advisor - Keyveve Technical Challenge

A full-stack travel advisory application that allows users to maintain a list of travel destinations, add personal notes about destinations, and ask AI-powered questions about their destinations.

## 🚀 Project Overview

This application implements a complete AI-powered travel advisory system with the following core features:

- **Destination Management**: Add, view, and delete travel destinations
- **Knowledge Base**: Add and manage personal notes/articles about destinations
- **AI Question & Answer**: Ask questions about destinations and get AI responses combining local knowledge and real-time data

## 🏗️ Architecture

### Backend (FastAPI)

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Integration**: OpenAI GPT with LangChain for RAG (Retrieval-Augmented Generation)
- **Weather API**: Open-Meteo for real-time weather data
- **Geocoding**: Nominatim for location coordinates
- **Vector Store**: FAISS for semantic search of knowledge base

### Frontend (Streamlit)

- **Framework**: Streamlit with custom CSS styling
- **Pages**: Destinations, Knowledge Base, and AI Q&A interface
- **API Communication**: RESTful API calls to backend

### Database Schema

```sql
-- Destinations table
destinations (id, name, created_at)

-- Knowledge base table
knowledge_base (id, destination_id, content, created_at)
```

## 📋 Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** installed
2. **PostgreSQL** database running
3. **OpenAI API Key** for AI functionality
4. **Internet connection** for external APIs (weather, geocoding)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd anurag-keyveve-challenge
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```bash
cp env.example .env
```

Edit the `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/travel_advisor

# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: OpenWeatherMap API Key (if you want to use OpenWeatherMap instead of open-meteo)
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here

# Backend Configuration
BACKEND_HOST=localhost
BACKEND_PORT=8000

# Frontend Configuration
FRONTEND_PORT=8501
```

### 4. Database Setup

```bash
# Run database migrations
python setup_database.py
```

### 5. Start the Application

#### Option A: Run Both Services Separately

**Terminal 1 - Backend:**

```bash
python run_backend.py
```

**Terminal 2 - Frontend:**

```bash
python run_frontend.py
```

#### Option B: Manual Service Start

**Backend:**

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
streamlit run app.py --server.port 8501
```

## 🌐 Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Destinations

- `GET /api/v1/destinations` - Get all destinations
- `POST /api/v1/destinations` - Create new destination
- `DELETE /api/v1/destinations/{id}` - Delete destination

### Knowledge Base

- `GET /api/v1/destinations/{id}/notes` - Get notes for destination
- `POST /api/v1/destinations/{id}/notes` - Create new note

### AI Query

- `POST /api/v1/ask` - Ask AI question about destination

### System

- `GET /health` - Health check

## 🎯 Usage Example

1. **Add a Destination**: Navigate to "Destinations" page and add "Paris"
2. **Add Knowledge**: Go to "Knowledge Base" page, select Paris, and add: "The Louvre is a world-famous museum in Paris with over 38,000 objects from prehistory to the 21st century."
3. **Ask AI**: Go to "Ask AI" page, select Paris, and ask: "What's the best museum to visit in Paris and how's the weather?"
4. **Get Response**: The AI will combine your knowledge about museums with real-time weather data

## 🔧 Technical Implementation Details

### AI Service Architecture

- **RAG Implementation**: Uses FAISS vector store for semantic search of knowledge base
- **LangChain Agent**: Combines local knowledge with external weather data
- **Error Handling**: Robust error handling with fallback responses
- **Rate Limiting**: Built-in rate limiting for API endpoints

### Database Features

- **Connection Pooling**: Optimized PostgreSQL connection management
- **Migrations**: Alembic for database schema management
- **Cascade Deletes**: Automatic cleanup of related data
- **Validation**: Input validation and error handling

### Frontend Features

- **Responsive Design**: Mobile-friendly interface
- **Real-time Chat**: Chat-style Q&A interface
- **Error Handling**: User-friendly error messages

## 🧪 Testing

The application includes comprehensive error handling and validation:

- **Startup Validation**: Validates all dependencies before starting
- **Database Validation**: Connection testing and health checks
- **API Validation**: Input validation and error responses
- **External Service Validation**: Weather and geocoding service checks

## 📊 Monitoring & Logging

- **Structured Logging**: Comprehensive logging with different levels
- **Health Checks**: Built-in health and readiness endpoints

## 🔒 Security Features

- **Rate Limiting**: Prevents API abuse
- **Error Handling**: Secure error messages without information leakage
- **CORS Configuration**: Proper CORS setup for cross-origin requests

## 🚀 Deployment Considerations

### Production Environment Variables

```env
ENVIRONMENT=production
WORKERS=4
LOG_LEVEL=warning
RELOAD=false
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

2. **OpenAI API Error**

   - Verify OPENAI_API_KEY is valid
   - Check API quota and billing
   - Ensure internet connectivity

3. **Weather API Issues**
   - Check internet connectivity
   - Verify geocoding service availability
   - Check rate limits

### Logs

- Backend logs: `backend.log`
- Console output for real-time debugging
- Health check endpoint for service status

## 📈 Performance Features

- **Connection Pooling**: Efficient database connection management
- **Caching**: Vector store caching for AI responses
- **Rate Limiting**: Prevents system overload
- **Async Operations**: Non-blocking API operations
- **Error Recovery**: Automatic retry mechanisms

## 🔮 Future Enhancements

Potential improvements for production deployment:

- **User Authentication**: JWT-based authentication system
- **Redis Caching**: Distributed caching for better performance
- **Docker Compose**: Container orchestration
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Prometheus/Grafana integration
- **Load Balancing**: Multiple backend instances
- **Database Optimization**: Query optimization and indexing

## 📝 Development Notes

### Code Structure

```
├── backend/           # FastAPI backend
│   ├── models.py     # SQLAlchemy models
│   ├── routes.py     # API endpoints
│   ├── ai_service.py # AI and RAG implementation
│   ├── database.py   # Database configuration
│   └── utils.py     # Utility functions
├── frontend/         # Streamlit frontend
│   ├── app.py       # Main application
│   └── config.py    # Configuration
├── db/              # Database migrations
└── requirements.txt # Dependencies
```

### Key Design Decisions

1. **RAG Implementation**: Uses FAISS for efficient semantic search
2. **Agent Architecture**: LangChain agent for combining multiple data sources
3. **Error Handling**: Comprehensive error handling throughout the stack
4. **Rate Limiting**: Built-in protection against API abuse
5. **Modular Design**: Clean separation of concerns

## 📄 License

This project is part of the Keyveve Technical Challenge assessment.

---

**Note**: This application is designed for demonstration purposes. For production use, additional security measures, authentication, and monitoring should be implemented.
