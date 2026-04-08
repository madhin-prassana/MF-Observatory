import React, { useEffect, useState, useCallback } from 'react';
import { getAllFunds } from '../services/api';
import FundCard from '../components/fundcard';
import LoadingSpinner from '../components/LoadingSpinner';

const FundExplorer = () => {
  const [funds, setFunds] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: '',
    risk_category: '',
    anomaly_status: '',
    sort_by: 'recommended_return',
    sort_order: 'desc',
  });

  const fetchFunds = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 100, ...filters };
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });
      const response = await getAllFunds(params);
      setFunds(response.data.funds);
      setTotalCount(response.data.total);
    } catch (error) {
      console.error('Error fetching funds:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchFunds();
    }, 300);
    return () => clearTimeout(debounceTimer);
  }, [fetchFunds]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      risk_category: '',
      anomaly_status: '',
      sort_by: 'recommended_return',
      sort_order: 'desc',
    });
  };

  const selectClasses =
    'w-full px-3 py-2.5 bg-[#1a1c2e] border border-white/10 rounded-lg text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all appearance-none';
  const labelClasses = 'block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider';

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Fund Explorer</h1>
          <p className="text-gray-400">
            Detailed view of all funds with current NAV and predicted returns.
          </p>
        </div>

        {/* Filters */}
        <div className="glass-card p-5 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className={labelClasses}>Search Fund</label>
              <div className="relative">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  placeholder="Search by name..."
                  className="w-full pl-10 pr-3 py-2.5 bg-[#1a1c2e] border border-white/10 rounded-lg text-gray-200 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all"
                />
              </div>
            </div>

            {/* Risk Category */}
            <div>
              <label className={labelClasses}>Risk Level</label>
              <select
                value={filters.risk_category}
                onChange={(e) => handleFilterChange('risk_category', e.target.value)}
                className={selectClasses}
              >
                <option value="">All Risks</option>
                <option value="Very Low Risk">Very Low Risk</option>
                <option value="Low Risk">Low Risk</option>
                <option value="Moderate Risk">Moderate Risk</option>
                <option value="High Risk">High Risk</option>
                <option value="Very High Risk">Very High Risk</option>
              </select>
            </div>

            {/* Anomaly Status */}
            <div>
              <label className={labelClasses}>Status</label>
              <select
                value={filters.anomaly_status}
                onChange={(e) => handleFilterChange('anomaly_status', e.target.value)}
                className={selectClasses}
              >
                <option value="">All Funds</option>
                <option value="normal">Normal Only</option>
                <option value="flagged">Flagged Only</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className={labelClasses}>Sort By</label>
              <select
                value={filters.sort_by}
                onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                className={selectClasses}
              >
                <option value="recommended_return">Predicted Return</option>
                <option value="volatility">Volatility</option>
                <option value="scheme_name">Name</option>
              </select>
            </div>
          </div>

          {/* Reset + Count */}
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {!loading && `${totalCount} fund${totalCount !== 1 ? 's' : ''} found`}
            </span>
            <button
              onClick={resetFilters}
              className="text-sm text-gray-400 hover:text-white px-4 py-1.5 rounded-lg hover:bg-white/5 transition-all"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <LoadingSpinner message="Loading funds..." />
        ) : funds.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-gray-400 text-lg mb-4">No funds found matching your criteria.</p>
            <button
              onClick={resetFilters}
              className="bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded-lg transition-colors"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-500">
              Showing {funds.length} of {totalCount} fund{totalCount !== 1 ? 's' : ''}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {funds.map((fund) => (
                <FundCard key={fund.scheme_code} fund={fund} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FundExplorer;