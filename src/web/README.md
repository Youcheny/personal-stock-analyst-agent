# 🌐 Value Agent Web Interface

A modern, responsive web interface for the Value Agent AI-powered stock research system. Built with Flask, Tailwind CSS, and Chart.js.

## ✨ Features

- **🔍 Smart Stock Search**: Type-ahead search with dropdown suggestions
- **📊 Performance Charts**: Interactive 1-year stock performance visualization
- **⚡ Asynchronous Analysis**: Real-time loading of different analysis sections
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **🎨 Modern UI**: Clean, professional interface inspired by Robinhood/Apple Stocks
- **📈 Real-time Updates**: Live status indicators for each analysis section

## 🚀 Quick Start

### Local Development

1. **Install web dependencies**:
   ```bash
   pip install -r web_requirements.txt
   ```

2. **Start the web interface**:
   ```bash
   ./start_web.sh
   ```
   
   Or manually:
   ```bash
   source .venv/bin/activate
   python src/web/app.py
   ```

3. **Open your browser**:
   ```
   http://localhost:5001
   ```

### Vercel Deployment

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Set environment variables** in Vercel dashboard:
   - `OPENAI_API_KEY`
   - `SEC_USER_AGENT`
   - `POLYGON_API_KEY` (optional)

## 🏗️ Architecture

```
Web Interface (Flask)
    ↓
├── Stock Search API → Mock stock database
├── Performance API → yfinance historical data
├── Analysis APIs → Value Agent orchestrator
    ↓
├── Business Overview → Company profile & description
├── Quick Facts → Financial metrics (FCF, ROIC, margins)
├── Risk Analysis → AI-powered risk assessment
├── Tech Analysis → Sector-specific insights
├── Financials Analysis → Financial health analysis
    ↓
Frontend (HTML/CSS/JS)
    ↓
├── Search Interface → Stock selection
├── Dashboard → Analysis display
├── Charts → Performance visualization
└── Responsive Layout → Mobile-friendly design
```

## 📁 File Structure

```
├── src/web/
│   ├── app.py             # Flask application
│   ├── templates/
│   │   └── index.html     # Main HTML template
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css  # Custom styles
│   │   └── js/
│   │       └── app.js     # Frontend JavaScript
│   ├── requirements.txt   # Web dependencies
│   └── __init__.py        # Package initialization
├── vercel.json            # Vercel configuration
└── start_web.sh           # Local startup script
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for AI-powered analysis
- `SEC_USER_AGENT`: User agent for SEC filings (optional)
- `POLYGON_API_KEY`: Alternative market data source (optional)

### API Endpoints

- `GET /` - Main interface
- `GET /api/search_stocks?q=<query>` - Stock search
- `GET /api/stock/<symbol>` - Basic stock info
- `GET /api/stock/<symbol>/performance` - Performance data
- `GET /api/analysis/<symbol>/<section>` - Analysis sections

## 🎨 UI Components

### Search Interface
- **Type-ahead search** with 300ms debouncing
- **Dropdown results** with company info
- **Keyboard navigation** support

### Dashboard Layout
- **Stock header** with basic info
- **Performance chart** using Chart.js
- **Analysis grid** with loading states
- **Status indicators** for each section

### Analysis Sections
- **Business Overview**: Company profile & description
- **Quick Facts**: Key financial metrics
- **Risk Analysis**: AI-powered risk assessment
- **Tech Analysis**: Sector-specific insights
- **Financials Analysis**: Financial health analysis

## 📱 Responsive Design

- **Mobile-first** approach
- **Grid layout** that adapts to screen size
- **Touch-friendly** interactions
- **Optimized charts** for small screens

## 🚀 Performance Features

- **Asynchronous loading** of analysis sections
- **Concurrency control** (3 parallel requests)
- **Debounced search** to reduce API calls
- **Skeleton loading** states
- **Error handling** with fallbacks

## 🔒 Security

- **CORS enabled** for cross-origin requests
- **Input validation** on all endpoints
- **Error sanitization** to prevent information leakage
- **Rate limiting** considerations in analysis queue

## 🧪 Testing

### Manual Testing
1. Search for stocks (AAPL, MSFT, GOOGL)
2. Verify all analysis sections load
3. Check responsive design on mobile
4. Test error handling with invalid symbols

### Browser Compatibility
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## 🚀 Deployment Options

### Vercel (Recommended)
- **Serverless** deployment
- **Global CDN** for fast loading
- **Automatic scaling**
- **Easy environment variable management**

### Other Platforms
- **Heroku**: Add `Procfile` with `web: gunicorn web_app:app`
- **Railway**: Direct Python deployment
- **DigitalOcean App Platform**: Container deployment
- **AWS/GCP**: Container or server deployment

## 🔮 Future Enhancements

- **Real-time stock updates** with WebSocket
- **Portfolio tracking** and watchlists
- **Advanced charting** with technical indicators
- **Export functionality** (PDF, Excel)
- **User authentication** and saved reports
- **Mobile app** using React Native or Flutter

## 🐛 Troubleshooting

### Common Issues

1. **"Value Agent not initialized"**
   - Check environment variables
   - Verify API keys are valid

2. **Analysis sections not loading**
   - Check browser console for errors
   - Verify network connectivity
   - Check API rate limits

3. **Charts not displaying**
   - Ensure Chart.js is loaded
   - Check for JavaScript errors
   - Verify data format from API

### Debug Mode

Enable debug mode in `web_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📞 Support

For issues or questions:
1. Check the browser console for errors
2. Verify environment variables are set
3. Test with a simple stock like "AAPL"
4. Check the main Value Agent README for setup

---

**Built with ❤️ using Flask, Tailwind CSS, and Chart.js**
