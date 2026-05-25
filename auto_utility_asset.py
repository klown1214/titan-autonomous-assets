"""
Revenue Data Processing Utility
A comprehensive tool for analyzing revenue data with multiple analysis capabilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import json
import csv
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import io
warnings.filterwarnings('ignore')

class RevenueProcessor:
    """
    Main class for processing and analyzing revenue data
    """
    
    def __init__(self, data_source: str = None, dataframe: pd.DataFrame = None):
        """
        Initialize RevenueProcessor
        
        Args:
            data_source: Path to CSV/Excel file or database connection string
            dataframe: Existing pandas DataFrame (alternative to data_source)
        """
        if dataframe is not None:
            self.df = dataframe.copy()
        elif data_source:
            self._load_data(data_source)
        else:
            self.df = pd.DataFrame()
        
        # Revenue metrics dictionary
        self.metrics = {}
        
    def _load_data(self, source: str) -> None:
        """Load data from various sources"""
        try:
            if source.endswith('.csv'):
                self.df = pd.read_csv(source)
            elif source.endswith('.xlsx') or source.endswith('.xls'):
                self.df = pd.read_excel(source)
            else:
                # Try generic loading
                self.df = pd.read_csv(source, error_bad_lines=False)
        except Exception as e:
            raise ValueError(f"Failed to load data from {source}: {str(e)}")
    
    def clean_data(self, 
                   date_column: str = 'date',
                   revenue_column: str = 'revenue',
                   cost_column: str = 'cost',
                   product_column: str = 'product',
                   region_column: str = 'region') -> pd.DataFrame:
        """
        Clean and preprocess revenue data
        
        Args:
            date_column: Name of date column
            revenue_column: Name of revenue column
            cost_column: Name of cost column
            product_column: Name of product column
            region_column: Name of region column
            
        Returns:
            Cleaned DataFrame
        """
        df = self.df.copy()
        
        # Standardize column names
        column_mapping = {
            'date': date_column,
            'revenue': revenue_column,
            'cost': cost_column,
            'product': product_column,
            'region': region_column,
            'quantity': 'quantity',
            'customer_id': 'customer_id',
            'transaction_id': 'transaction_id'
        }
        
        # Rename columns to standardized names
        df = df.rename(columns={v: k for k, v in column_mapping.items() if v in df.columns})
        
        # Convert date column
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['revenue', 'cost', 'quantity']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing critical values
        critical_cols = ['date', 'revenue']
        df = df.dropna(subset=critical_cols)
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        self.df = df
        return df
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate key revenue metrics
        
        Returns:
            Dictionary of calculated metrics
        """
        if self.df.empty:
            return {}
        
        df = self.df.copy()
        
        # Basic metrics
        total_revenue = df['revenue'].sum()
        total_cost = df['cost'].sum() if 'cost' in df.columns else 0
        total_profit = total_revenue - total_cost
        avg_transaction_value = df['revenue'].mean()
        total_transactions = len(df)
        
        # Time-based metrics
        if 'date' in df.columns:
            df['month'] = df['date'].dt.to_period('M')
            monthly_revenue = df.groupby('month')['revenue'].sum()
            best_month = monthly_revenue.idxmax() if not monthly_revenue.empty else None
            worst_month = monthly_revenue.idxmin() if not monthly_revenue.empty else None
            
            # Growth metrics
            recent_months = monthly_revenue.tail(3).sum()
            earlier_months = monthly_revenue.head(3).sum() if len(monthly_revenue) > 3 else 0
            growth_rate = ((recent_months - earlier_months) / earlier_months * 100 
                          if earlier_months > 0 else 0)
        else:
            best_month = worst_month = growth_rate = None
        
        # Product metrics
        top_products = bottom_products = None
        product_performance = []
        if 'product' in df.columns:
            product_performance = df.groupby('product').agg({
                'revenue': 'sum',
                'cost': 'sum' if 'cost' in df.columns else 0
            }).reset_index()
            product_performance['profit'] = (product_performance['revenue'] - 
                                            product_performance['cost'])
            product_performance = product_performance.sort_values('revenue', ascending=False)
            top_products = product_performance.head(5)
            bottom_products = product_performance.tail(5)
        
        # Regional metrics
        region_performance = None
        if 'region' in df.columns:
            region_performance = df.groupby('region').agg({
                'revenue': 'sum'
            }).reset_index()
            region_performance.columns = ['region', 'revenue']
            region_performance = region_performance.sort_values('revenue', ascending=False)
        
        # Customer metrics
        high_value_customers = None
        if 'customer_id' in df.columns:
            customer_value = df.groupby('customer_id')['revenue'].agg(['sum', 'count'])
            customer_value.columns = ['total_spent', 'transactions']
            customer_value = customer_value.reset_index()
            customer_value['avg_order_value'] = (customer_value['total_spent'] / 
                                                customer_value['transactions'])
            high_value_customers = customer_value.nlargest(10, 'total_spent')
        
        # Calculate profitability metrics
        if total_revenue > 0:
            profit_margin = (total_profit / total_revenue) * 100
            avg_profit_per_transaction = total_profit / total_transactions
        else:
            profit_margin = avg_profit_per_transaction = 0
        
        metrics = {
            'summary': {
                'total_revenue': round(total_revenue, 2),
                'total_cost': round(total_cost, 2),
                'total_profit': round(total_profit, 2),
                'profit_margin': round(profit_margin, 2),
                'avg_transaction_value': round(avg_transaction_value, 2),
                'avg_profit_per_transaction': round(avg_profit_per_transaction, 2),
                'total_transactions': total_transactions,
                'growth_rate': round(growth_rate, 2)
            },
            'time_analysis': {
                'best_month': str(best_month) if best_month else None,
                'worst_month': str(worst_month) if worst_month else None,
                'monthly_revenue': monthly_revenue.to_dict() if 'monthly_revenue' in locals() else {}
            },
            'product_analysis': {
                'top_products': top_products.to_dict('records') if top_products is not None else [],
                'bottom_products': bottom_products.to_dict('records') if bottom_products is not None else [],
                'product_performance': product_performance.to_dict('records') if not product_performance.empty else []
            },
            'regional_analysis': region_performance.to_dict('records') if region_performance is not None else [],
            'customer_analysis': {
                'high_value_customers': high_value_customers.to_dict('records') if high_value_customers is not None else []
            }
        }
        
        self.metrics = metrics
        return metrics
    
    def forecast_revenue(self, 
                        periods: int = 6, 
                        method: str = 'holtwinters',
                        seasonal_periods: int = 12) -> pd.DataFrame:
        """
        Forecast future revenue using time series analysis
        
        Args:
            periods: Number of periods to forecast
            method: Forecasting method ('holtwinters', 'arima', 'exp_smooth')
            seasonal_periods: Seasonal periods for Holt-Winters
            
        Returns:
            DataFrame with historical and forecasted values
        """
        if 'date' not in self.df.columns or 'revenue' not in self.df.columns:
            raise ValueError("Date and revenue columns are required for forecasting")
        
        df = self.df.copy()
        df = df.sort_values('date')
        df = df.set_index('date')
        
        # Resample to monthly if not already
        if df.index.freq is None:
            df = df.resample('M').sum()
        
        historical = df['revenue'].copy()
        
        try:
            if method == 'holtwinters':
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                model = ExponentialSmoothing(
                    historical,
                    seasonal_periods=seasonal_periods,
                    trend='add',
                    seasonal='add'
                ).fit()
                forecast = model.forecast(periods)
                
            elif method == 'arima':
                from statsmodels.tsa.arima.model import ARIMA
                model = ARIMA(historical, order=(1, 1, 1))
                model_fit = model.fit()
                forecast = model_fit.forecast(steps=periods)
                
            elif method == 'exp_smooth':
                from statsmodels.tsa.exponential_smoothing import ExponentialSmoothing
                model = ExponentialSmoothing(historical, trend='add').fit()
                forecast = model.forecast(periods)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Create forecast DataFrame
            forecast_index = pd.date_range(
                start=historical.index[-1] + pd.DateOffset(months=1),
                periods=periods,
                freq='M'
            )
            
            forecast_df = pd.DataFrame({
                'date': forecast_index,
                'revenue': forecast.values,
                'type': 'forecast'
            })
            
            # Add historical data
            historical_df = pd.DataFrame({
                'date': historical.index,
                'revenue': historical.values,
                'type': 'historical'
            })
            
            result = pd.concat([historical_df, forecast_df], ignore_index=True)
            result['month'] = result['date'].dt.to_period('M')
            
            return result
            
        except Exception as e:
            print(f"Forecasting failed: {str(e)}")
            return pd.DataFrame()
    
    def analyze_product_performance(self, 
                                   top_n: int = 10,
                                   sort_by: str = 'revenue') -> pd.DataFrame:
        """
        Analyze product performance
        
        Args:
            top_n: Number of top products to show
            sort_by: Sort by 'revenue', 'profit', or 'margin'
            
        Returns:
            DataFrame with product performance metrics
        """
        if 'product' not in self.df.columns:
            raise ValueError("Product column is required")
        
        df = self.df.copy()
        
        # Calculate product metrics
        agg_dict = {'revenue': 'sum'}
        if 'cost' in df.columns:
            agg_dict['cost'] = 'sum'
        if 'transaction_id' in df.columns:
            agg_dict['transaction_id'] = 'count'
        else:
            agg_dict['quantity'] = 'sum'
        
        product_stats = df.groupby('product').agg(agg_dict).reset_index()
        
        if 'transaction_id' in product_stats.columns:
            product_stats.rename(columns={'transaction_id': 'transactions'}, inplace=True)
        elif 'quantity' in product_stats.columns:
            product_stats.rename(columns={'quantity': 'transactions'}, inplace=True)
        else:
            product_stats['transactions'] = len(df) / len(product_stats)
        
        if 'cost' not in product_stats.columns:
            product_stats['cost'] = 0
        
        product_stats['profit'] = product_stats['revenue'] - product_stats['cost']
        product_stats['profit_margin'] = (product_stats['profit'] / product_stats['revenue'] * 100).fillna(0)
        product_stats['avg_price'] = product_stats['revenue'] / product_stats['transactions']
        
        # Sort and select top_n
        if sort_by == 'margin':
            product_stats = product_stats.sort_values('profit_margin', ascending=False)
        else:
            product_stats = product_stats.sort_values(sort_by, ascending=False)
        
        return product_stats.head(top_n)
    
    def detect_anomalies(self, 
                        column: str = 'revenue',
                        method: str = 'iqr',
                        threshold: float = 1.5) -> pd.DataFrame:
        """
        Detect anomalies in revenue data
        
        Args:
            column: Column to analyze
            method: Detection method ('iqr', 'zscore', 'iforest')
            threshold: Threshold for detection
            
        Returns:
            DataFrame with anomalies flagged
        """
        df = self.df.copy()
        
        if column not in df.columns:
            raise ValueError(f"Column {column} not found")
        
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            anomalies = df[(df[column] < lower_bound) | (df[column] > upper_bound)].copy()
            
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df[column].fillna(df[column].mean())))
            anomalies = df[z_scores > threshold].copy()
            
        elif method == 'iforest':
            from sklearn.ensemble import IsolationForest
            model = IsolationForest(contamination=0.1)
            df['anomaly'] = model.fit_predict(df[[column]].fillna(0).values)
            anomalies = df[df['anomaly'] == -1].drop('anomaly', axis=1).copy()
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return anomalies
    
    def generate_report(self, 
                       output_format: str = 'json',
                       include_charts: bool = True) -> str:
        """
        Generate comprehensive revenue report
        
        Args:
            output_format: Output format ('json', 'csv', 'html')
            include_charts: Whether to include chart data
            
        Returns:
            Report as string
        """
        metrics = self.calculate_metrics()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'total_records': len(self.df),
                'date_range': {
                    'start': str(self.df['date'].min()) if 'date' in self.df.columns else None,
                    'end': str(self.df['date'].max()) if 'date' in self.df.columns else None
                }
            },
            'key_metrics': metrics.get('summary', {}),
            'time_analysis': metrics.get('time_analysis', {}),
            'product_analysis': metrics.get('product_analysis', {}),
            'regional_analysis': metrics.get('regional_analysis', {}),
            'customer_analysis': metrics.get('customer_analysis', {})
        }
        
        if output_format == 'json':
            return json.dumps(report, indent=2, default=str)
        
        elif output_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Metric', 'Value'])
            for category, items in metrics.items():
                for key, value in items.items():
                    if isinstance(value, (int, float, str)):
                        writer.writerow([f"{category}_{key}", value])
            return output.getvalue()
        
        elif output_format == 'html':
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Revenue Report - {datetime.now().strftime('%Y-%m-%d')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .metric {{ background: #f5f5f5; padding: 10px; margin: 5px; border-radius: 5px; }}
                    .section {{ margin: 20px 0; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; }}
                </style>
            </head>
            <body>
                <h1>Revenue Analysis Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
            
            for category, items in report.items():
                html += f"<div class='section'><h2>{category.replace('_', ' ').title()}</h2>"
                if isinstance(items, dict):
                    for key, value in items.items():
                        if isinstance(value, (int, float, str)):
                            html += f"<div class='metric'><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>"
                html += "</div>"
            
            html += "</body></html>"
            return html
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def visualize_revenue(self, 
                         save_path: str = None,
                         figsize: tuple = (15, 10)) -> Dict[str, plt.Figure]:
        """
        Create revenue visualizations
        
        Args:
            save_path: Path to save figures (optional)
            figsize: Figure size
            
        Returns:
            Dictionary of created figures
        """
        figures = {}
        df = self.df.copy()
        
        if 'date' in df.columns and 'revenue' in df.columns:
            fig1, ax1 = plt.subplots(figsize=figsize)
            df.groupby('date')['revenue'].sum().plot(kind='line', ax=ax1)
            ax1.set_title('Revenue Over Time')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Revenue')
            ax1.grid(True, alpha=0.3)
            figures['revenue_over_time'] = fig1
            
            if df['date'].nunique() > 1:
                df['month'] = df['date'].dt.to_period('M')
                df['year'] = df['date'].dt.year
                monthly_data = df.groupby(['month', 'year'])['revenue'].sum().unstack()
                if not monthly_data.empty:
                    fig2, ax2 = plt.subplots(figsize=(12, 6))
                    sns.heatmap(monthly_data.fillna(0), ax=ax2, cmap='YlOrRd')
                    ax2.set_title('Monthly Revenue Heatmap')
                    figures['monthly_heatmap'] = fig2
        
        if 'product' in df.columns:
            top_products = self.analyze_product_performance(top_n=10)
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            ax3.barh(top_products['product'], top_products['revenue'])
            ax3.set_title('Top 10 Products by Revenue')
            ax3.set_xlabel('Revenue')
            ax3.invert_yaxis()
            figures['top_products'] = fig3
        
        if 'product' in df.columns and 'cost' in df.columns:
            product_profit = df.groupby('product').agg({
                'revenue': 'sum',
                'cost': 'sum'
            }).reset_index()
            product_profit['profit_margin'] = (product_profit['revenue'] - product_profit['cost']) / product_profit['revenue'].replace(0, 1) * 100
            
            fig4, ax4 = plt.subplots(figsize=(12, 6))
            bars = ax4.bar(product_profit['product'], product_profit['profit_margin'])
            ax4.set_title('Profit Margin by Product')
            ax4.set_ylabel('Profit Margin (%)')
            ax4.set_xlabel('Product')
            ax4.tick_params(axis='x', rotation=45)
            
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            figures['profit_margin'] = fig4
        
        if save_path:
            for name, fig in figures.items():
                fig.savefig(f"{save_path}_{name}.png", dpi=300, bbox_inches='tight')
            plt.close('all')
        
        return figures
    
    def export_to_excel(self, 
                       output_path: str, 
                       include_charts: bool = False) -> None:
        """
        Export analysis to Excel workbook
        
        Args:
            output_path: Output Excel file path
            include_charts: Whether to include charts in Excel
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            self.df.to_excel(writer, sheet_name='Raw Data', index=False)
            
            metrics = self.calculate_metrics()
            metrics_data = [['Metric', 'Value']]
            for category, items in metrics.items():
                for key, value in items.items():
                    if isinstance(value, (int, float)):
                        metrics_data.append([f"{category}_{key}", value])
            
            metrics_df = pd.DataFrame(metrics_data[1:], columns=['Metric', 'Value'])
            metrics_df.to_excel(writer, sheet_name='Key Metrics', index=False)
            
            if metrics.get('product_analysis', {}).get('product_performance'):
                product_df = pd.DataFrame(metrics['product_analysis']['product_performance'])
                product_df.to_excel(writer, sheet_name='Product Analysis', index=False)
            
            if metrics.get('regional_analysis'):
                regional_df = pd.DataFrame(metrics['regional_analysis'])
                regional_df.to_excel(writer, sheet_name='Regional Analysis', index=False)
            
            if metrics.get('customer_analysis', {}).get('high_value_customers'):
                customer_df = pd.DataFrame(metrics['customer_analysis']['high_value_customers'])
                customer_df.to_excel(writer, sheet_name='Customer Analysis', index=False)
    
    def benchmark(self, 
                 industry_benchmarks: Dict[str, float]) -> Dict[str, str]:
        """
        Compare metrics against industry benchmarks
        
        Args:
            industry_benchmarks: Dictionary of industry benchmark values
            
        Returns:
            Dictionary of comparison results
        """
        metrics = self.calculate_metrics()['summary']
        comparison = {}
        
        benchmarks = {
            'profit_margin': industry_benchmarks.get('profit_margin', 0),
            'avg_transaction_value': industry_benchmarks.get('avg_transaction_value', 0),
            'growth_rate': industry_benchmarks.get('growth_rate', 0)
        }
        
        for metric, benchmark in benchmarks.items():
            if metric in metrics and benchmark > 0:
                actual = metrics[metric]
                if actual > benchmark:
                    comparison[metric] = 'Above Benchmark'
                elif actual < benchmark:
                    comparison[metric] = 'Below Benchmark'
                else:
                    comparison[metric] = 'At Benchmark'
        
        return comparison


def example_usage():
    sample_data = {
        'date': pd.date_range('2023-01-01', periods=100, freq='D').tolist() * 3,
        'product': ['Product A', 'Product B', 'Product C'] * 100,
        'region': ['North', 'South', 'East', 'West'] * 75,
        'revenue': np.random.normal(100, 25, 300).tolist(),
        'cost': np.random.normal(60, 15, 300).tolist(),
        'quantity': np.random.randint(1, 10, 300).tolist(),
        'customer_id': np.random.randint(1000, 2000, 300).tolist()
    }
    
    df = pd.DataFrame(sample_data)
    processor = RevenueProcessor(dataframe=df)
    processor.clean_data()
    
    metrics = processor.calculate_metrics()
    print("Key Metrics:")
    print(json.dumps(metrics['summary'], indent=2))
    
    forecast = processor.forecast_revenue(periods=3)
    print("\nForecast:")
    print(forecast.tail())
    
    anomalies = processor.detect_anomalies(method='iqr')
    print(f"\nDetected {len(anomalies)} anomalies")
    
    report = processor.generate_report(output_format='json')
    print("\nReport sample:")
    print(report[:500] + "...")
    
    figures = processor.visualize_revenue()
    print(f"\nCreated {len(figures)} visualizations")
    
    processor.export_to_excel('revenue_analysis.xlsx', include_charts=True)
    print("\nExported to Excel")
    
    return processor


if __name__ == "__main__":
    processor = example_usage()
    
    print("\n" + "="*50)
    print("Additional Analysis Examples:")
    print("="*50)
    
    product_analysis = processor.analyze_product_performance(top_n=5)
    print("\nTop 5 Products:")
    print(product_analysis.to_string(index=False))
    
    industry_standards = {
        'profit_margin': 25.0,
        'avg_transaction_value': 120.0,
        'growth_rate': 5.0
    }
    
    benchmark_results = processor.benchmark(industry_standards)
    print("\nBenchmark Results:")
    for metric, result in benchmark_results.items():
        print(f"{metric.replace('_', ' ').title()}: {result}")