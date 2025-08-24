// Value Agent Web Interface JavaScript

class ValueAgentApp {
    constructor() {
        this.currentStock = null;
        this.performanceChart = null;
        this.searchTimeout = null;
        this.analysisQueue = [];
        this.isAnalyzing = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupSearchResults();
    }

    bindEvents() {
        // Stock search input
        const searchInput = document.getElementById('stockSearch');
        searchInput.addEventListener('input', (e) => this.handleSearchInput(e));
        searchInput.addEventListener('focus', () => this.showSearchResults());
        searchInput.addEventListener('blur', () => this.hideSearchResultsDelayed());

        // Download report button
        const downloadBtn = document.getElementById('downloadReport');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadReport());
        }

        // Click outside to close search results
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#stockSearch') && !e.target.closest('#searchResults')) {
                this.hideSearchResults();
            }
        });
    }

    setupSearchResults() {
        const searchResults = document.getElementById('searchResults');
        searchResults.addEventListener('click', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (resultItem) {
                const symbol = resultItem.dataset.symbol;
                this.selectStock(symbol);
            }
        });
    }

    handleSearchInput(e) {
        const query = e.target.value.trim();
        
        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        if (query.length < 2) {
            this.hideSearchResults();
            return;
        }

        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    async performSearch(query) {
        try {
            const response = await fetch(`/api/search_stocks?q=${encodeURIComponent(query)}`);
            const stocks = await response.json();
            this.displaySearchResults(stocks);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    displaySearchResults(stocks) {
        const searchResults = document.getElementById('searchResults');
        
        if (stocks.length === 0) {
            searchResults.innerHTML = '<div class="p-4 text-gray-500 text-center">No stocks found</div>';
            searchResults.classList.remove('hidden');
            return;
        }

        const resultsHTML = stocks.map(stock => `
            <div class="search-result-item" data-symbol="${stock.symbol}">
                <div class="flex items-center justify-between">
                    <div>
                        <div class="font-semibold text-gray-900">${stock.symbol}</div>
                        <div class="text-sm text-gray-600">${stock.name}</div>
                    </div>
                    <div class="text-xs text-gray-500">${stock.sector}</div>
                </div>
            </div>
        `).join('');

        searchResults.innerHTML = resultsHTML;
        searchResults.classList.remove('hidden');
    }

    hideSearchResults() {
        const searchResults = document.getElementById('searchResults');
        searchResults.classList.add('hidden');
    }

    hideSearchResultsDelayed() {
        setTimeout(() => this.hideSearchResults(), 200);
    }

    async selectStock(symbol) {
        this.currentStock = symbol;
        this.hideSearchResults();
        this.showLoadingOverlay();
        
        // Clear search input
        document.getElementById('stockSearch').value = symbol;
        
        try {
            // Show dashboard
            this.showStockDashboard();
            
            // Start analysis
            await this.startAnalysis(symbol);
            
        } catch (error) {
            console.error('Error selecting stock:', error);
            this.showError('Failed to load stock data');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    showStockDashboard() {
        document.getElementById('welcomeMessage').classList.add('hidden');
        document.getElementById('stockDashboard').classList.remove('hidden');
        
        // Update stock header
        document.getElementById('stockSymbol').textContent = this.currentStock;
        document.getElementById('stockName').textContent = 'Loading...';
        document.getElementById('stockSector').textContent = 'Loading...';
        document.getElementById('stockPrice').textContent = '--';
        document.getElementById('stockChange').textContent = '--';
    }

    async startAnalysis(symbol) {
        // Initialize all analysis sections
        this.initializeAnalysisSections();
        
        // Start performance chart
        await this.loadPerformanceChart(symbol);
        
        // Queue all analysis sections
        const sections = [
            'business_overview',
            'quick_facts', 
            'risk_analysis',
            'tech_analysis',
            'financials_analysis'
        ];

        // Process sections with concurrency control
        await this.processAnalysisQueue(sections, symbol);
        
        // Generate full report
        await this.generateFullReport(symbol);
    }

    initializeAnalysisSections() {
        const sections = [
            'businessOverview',
            'quickFacts',
            'riskAnalysis', 
            'techAnalysis',
            'financialsAnalysis'
        ];

        sections.forEach(section => {
            const statusEl = document.getElementById(`${section}Status`);
            const contentEl = document.getElementById(`${section}Content`);
            
            if (statusEl) statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            if (contentEl) contentEl.innerHTML = this.getSkeletonHTML();
        });
    }

    getSkeletonHTML() {
        return `
            <div class="space-y-3">
                <div class="skeleton skeleton-text short"></div>
                <div class="skeleton skeleton-text medium"></div>
                <div class="skeleton skeleton-text long"></div>
                <div class="skeleton skeleton-text medium"></div>
            </div>
        `;
    }

    async processAnalysisQueue(sections, symbol) {
        // Process sections with limited concurrency
        const concurrency = 3;
        const chunks = [];
        
        for (let i = 0; i < sections.length; i += concurrency) {
            chunks.push(sections.slice(i, i + concurrency));
        }

        for (const chunk of chunks) {
            const promises = chunk.map(section => this.loadAnalysisSection(symbol, section));
            await Promise.allSettled(promises);
            
            // Small delay between chunks to avoid overwhelming the API
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    async loadAnalysisSection(symbol, section) {
        try {
            const response = await fetch(`/api/analysis/${symbol}/${section}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateAnalysisSection(section, data.data);
            this.updateSectionStatus(section, 'success');
            
        } catch (error) {
            console.error(`Error loading ${section}:`, error);
            this.updateAnalysisSection(section, { error: error.message });
            this.updateSectionStatus(section, 'error');
        }
    }

    updateAnalysisSection(section, data) {
        const contentEl = document.getElementById(this.getContentElementId(section));
        if (!contentEl) return;

        if (data.error) {
            contentEl.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
            return;
        }

        let html = '';
        
        switch (section) {
            case 'business_overview':
                html = this.renderBusinessOverview(data);
                // Update stock header with company info
                this.updateStockHeader(data);
                break;
            case 'quick_facts':
                html = this.renderQuickFacts(data);
                break;
            case 'risk_analysis':
                html = this.renderRiskAnalysis(data);
                break;
            case 'tech_analysis':
                html = this.renderTechAnalysis(data);
                break;
            case 'financials_analysis':
                html = this.renderFinancialsAnalysis(data);
                break;
        }

        contentEl.innerHTML = html;
        contentEl.classList.add('loaded');
    }

    getContentElementId(section) {
        const mapping = {
            'business_overview': 'businessOverviewContent',
            'quick_facts': 'quickFactsContent',
            'risk_analysis': 'riskAnalysisContent',
            'tech_analysis': 'techAnalysisContent',
            'financials_analysis': 'financialsAnalysisContent'
        };
        return mapping[section];
    }

    updateSectionStatus(section, status) {
        const statusEl = document.getElementById(this.getStatusElementId(section));
        if (!statusEl) return;

        const statusText = {
            'success': '<i class="fas fa-check-circle"></i> Complete',
            'error': '<i class="fas fa-exclamation-circle"></i> Error',
            'loading': '<i class="fas fa-spinner fa-spin"></i> Loading...'
        };

        statusEl.innerHTML = statusText[status];
        statusEl.className = `text-sm ${status === 'success' ? 'status-success' : status === 'error' ? 'status-error' : 'status-loading'}`;
    }

    getStatusElementId(section) {
        const mapping = {
            'business_overview': 'businessOverviewStatus',
            'quick_facts': 'quickFactsStatus',
            'risk_analysis': 'riskAnalysisStatus',
            'tech_analysis': 'techAnalysisStatus',
            'financials_analysis': 'financialsAnalysisStatus'
        };
        return mapping[section];
    }

    renderBusinessOverview(data) {
        return `
            <div class="analysis-content">
                <div class="space-y-3">
                    <div>
                        <h4 class="font-semibold text-gray-900">Company Name</h4>
                        <p class="text-gray-700">${data.name || 'N/A'}</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900">Sector</h4>
                        <p class="text-gray-700">${data.sector || 'N/A'}</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900">Industry</h4>
                        <p class="text-gray-700">${data.industry || 'N/A'}</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900">Business Summary</h4>
                        <div class="text-gray-700 markdown-content">
                            ${this.parseMarkdown(data.summary || 'No description available')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderQuickFacts(data) {
        const formatPercent = (value) => {
            if (value === null || value === undefined) return 'N/A';
            return typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : value;
        };

        return `
            <div class="analysis-content">
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700">FCF Yield (TTM)</span>
                        <span class="font-semibold text-gray-900">${formatPercent(data.fcf_yield)}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700">ROIC (Est.)</span>
                        <span class="font-semibold text-gray-900">${formatPercent(data.roic)}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700">Debt/Equity</span>
                        <span class="font-semibold text-gray-900">${data.debt_to_equity || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700">Gross Margin</span>
                        <span class="font-semibold text-gray-900">${formatPercent(data.gross_margin)}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700">Operating Margin</span>
                        <span class="font-semibold text-gray-900">${formatPercent(data.operating_margin)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderRiskAnalysis(data) {
        // Handle structured web data
        if (data && typeof data === 'object' && data.success) {
            const riskLevel = data.risk_level || 'Unknown';
            const riskLevelClass = {
                'High': 'text-red-600',
                'Medium': 'text-yellow-600',
                'Low': 'text-green-600'
            }[riskLevel] || 'text-gray-600';

            return `
                <div class="analysis-content">
                    <div class="mb-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm font-medium text-gray-500">Risk Level</span>
                            <span class="px-2 py-1 text-xs font-semibold rounded-full ${riskLevelClass} bg-gray-100">
                                ${riskLevel}
                            </span>
                        </div>
                        <div class="text-sm text-gray-600">${data.summary || 'Risk analysis available'}</div>
                    </div>
                    
                    <div class="space-y-3">
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-2">Key Risk Metrics</h4>
                            <div class="grid grid-cols-2 gap-2 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Debt/Equity:</span>
                                    <span class="font-medium">${data.key_metrics?.debt_to_equity || 'N/A'}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">FCF Yield:</span>
                                    <span class="font-medium">${this.formatPercent(data.key_metrics?.fcf_yield)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">ROIC:</span>
                                    <span class="font-medium">${this.formatPercent(data.key_metrics?.roic)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Gross Margin:</span>
                                    <span class="font-medium">${this.formatPercent(data.key_metrics?.gross_margin)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-2">Detailed Analysis</h4>
                            <div class="prose prose-sm max-w-none markdown-content">
                                ${this.parseMarkdown(data.content || 'No detailed analysis available')}
                            </div>
                        </div>
                        
                        ${data.note ? `<div class="text-xs text-gray-500 italic">${data.note}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Handle error cases
        if (data && data.error) {
            return `
                <div class="analysis-content">
                    <div class="error-message">Error: ${data.error}</div>
                </div>
            `;
        }
        
        // Fallback for old format
        if (typeof data === 'string') {
            return `<div class="analysis-content">${data}</div>`;
        }
        
        return `
            <div class="analysis-content">
                <div class="error-message">
                    Unexpected data format for risk analysis
                </div>
            </div>
        `;
    }

    renderTechAnalysis(data) {
        // Handle string data (original format)
        if (typeof data === 'string') {
            return `<div class="analysis-content markdown-content">${this.parseMarkdown(data)}</div>`;
        }
        
        // Handle error cases
        if (data && data.error) {
            return `
                <div class="analysis-content">
                    <div class="error-message">Error: ${data.error}</div>
                </div>
            `;
        }
        
        return `
            <div class="analysis-content">
                <div class="error-message">
                    Unexpected data format for tech analysis
                </div>
            </div>
        `;
    }

    renderFinancialsAnalysis(data) {
        // Handle string data (original format)
        if (typeof data === 'string') {
            return `<div class="analysis-content markdown-content">${this.parseMarkdown(data)}</div>`;
        }
        
        // Handle error cases
        if (data && data.error) {
            return `
                <div class="analysis-content">
                    <div class="error-message">Error: ${data.error}</div>
                </div>
            `;
        }
        
        return `
            <div class="analysis-content">
                <div class="error-message">
                    Unexpected data format for financials analysis
                </div>
            </div>
        `;
    }

    async loadPerformanceChart(symbol) {
        try {
            // Load both performance chart and current price
            const [performanceResponse, priceResponse] = await Promise.all([
                fetch(`/api/stock/${symbol}/performance`),
                fetch(`/api/stock/${symbol}/price`)
            ]);
            
            const performanceData = await performanceResponse.json();
            const priceData = await priceResponse.json();
            
            if (performanceData.error) {
                throw new Error(performanceData.error);
            }
            
            this.renderPerformanceChart(performanceData);
            
            // Update stock price display
            if (!priceData.error) {
                this.updateStockPrice(priceData);
            }
            
        } catch (error) {
            console.error('Error loading performance chart:', error);
            this.showChartError();
        }
    }

    renderPerformanceChart(data) {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.performanceChart) {
            this.performanceChart.destroy();
        }

        const chartData = {
            labels: data.performance.map(d => d.date),
            datasets: [{
                label: 'Stock Price',
                data: data.performance.map(d => d.close),
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        };

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Price ($)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    showChartError() {
        const chartContainer = document.getElementById('performanceChart');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="flex items-center justify-center h-full">
                    <div class="text-center text-gray-500">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>Failed to load performance data</p>
                    </div>
                </div>
            `;
        }
    }

    updateStockPrice(priceData) {
        const priceEl = document.getElementById('stockPrice');
        const changeEl = document.getElementById('stockChange');
        
        if (priceEl) {
            priceEl.textContent = `$${priceData.current_price.toFixed(2)}`;
        }
        
        if (changeEl) {
            const changeText = `${priceData.change >= 0 ? '+' : ''}${priceData.change.toFixed(2)} (${priceData.change_percent >= 0 ? '+' : ''}${priceData.change_percent.toFixed(2)}%)`;
            changeEl.textContent = changeText;
            changeEl.className = `text-sm font-medium ${priceData.change_direction === 'positive' ? 'text-green-600' : 'text-red-600'}`;
        }
    }

    updateStockHeader(companyData) {
        const nameEl = document.getElementById('stockName');
        const sectorEl = document.getElementById('stockSector');
        
        if (nameEl && companyData.name) {
            nameEl.textContent = companyData.name;
        }
        
        if (sectorEl && companyData.sector) {
            sectorEl.textContent = companyData.sector;
        }
    }

    async generateFullReport(symbol) {
        try {
            // For now, we'll just show a summary
            // In a full implementation, you'd call the orchestrator to generate a complete memo
            const fullReportContent = document.getElementById('fullReportContent');
            if (fullReportContent) {
                fullReportContent.innerHTML = `
                    <div class="analysis-content">
                        <p class="text-gray-600">
                            Analysis complete! All sections have been loaded above. 
                            Use the download button to save a PDF version of this report.
                        </p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error generating full report:', error);
        }
    }

    downloadReport() {
        // Placeholder for PDF generation
        alert('PDF download functionality would be implemented here');
    }

    showLoadingOverlay() {
        document.getElementById('loadingOverlay').classList.remove('hidden');
    }

    hideLoadingOverlay() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showError(message) {
        // You could implement a toast notification system here
        console.error(message);
        alert(message);
    }

    formatPercent(value) {
        if (value === null || value === undefined) return 'N/A';
        return typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : value;
    }

    // Simple markdown to HTML conversion
    parseMarkdown(content) {
        if (!content || typeof content !== 'string') {
            return content || 'No content available';
        }
        
        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true
        });
        
        // Parse markdown to HTML
        return marked.parse(content);
    }


}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ValueAgentApp();
});
