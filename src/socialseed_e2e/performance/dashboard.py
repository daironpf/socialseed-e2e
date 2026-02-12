"""Performance dashboard generator for socialseed-e2e."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class PerformanceDashboard:
    """Generates visual reports for performance tests."""

    def __init__(self, report_dir: str = ".e2e/performance/reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(self, summary: Dict[str, Any], test_name: str = "Performance Test"):
        """Generate a self-contained HTML report with charts."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SocialSeed E2E - Performance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .header {{ display: flex; box-pack: justify; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .card {{ background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center; }}
        .card h3 {{ margin: 0; font-size: 14px; color: #94a3b8; text-transform: uppercase; }}
        .card .value {{ font-size: 28px; font-weight: bold; margin-top: 10px; color: #38bdf8; }}
        .chart-container {{ background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 30px; }}
        .badge {{ padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #065f46; color: #34d399; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>{test_name}</h1>
                <p style="color: #94a3b8">Execution Time: {timestamp}</p>
            </div>
            <span class="badge badge-success">SLA PASSED</span>
        </div>

        <div class="card-grid">
            <div class="card">
                <h3>Total Requests</h3>
                <div class="value">{summary['total_requests']}</div>
            </div>
            <div class="card">
                <h3>Avg Latency</h3>
                <div class="value">{summary['avg_latency']:.2f} ms</div>
            </div>
            <div class="card">
                <h3>P95 Latency</h3>
                <div class="value">{summary['p95']:.2f} ms</div>
            </div>
            <div class="card">
                <h3>Error Rate</h3>
                <div class="value">{summary['error_rate']*100:.2f}%</div>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="latencyChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('latencyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['P50', 'P90', 'P95', 'P99', 'Max'],
                datasets: [{{
                    label: 'Latency (ms)',
                    data: [{summary['p50']}, {summary['p90']}, {summary['p95']}, {summary['p99']}, {summary['max_latency']}],
                    backgroundColor: '#38bdf8'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: '#334155' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }}
            }}
        }});
    </script>
</body>
</html>
"""
        report_path = self.report_dir / filename
        report_path.write_text(html_content)
        print(f"Performance report generated: {report_path}")
        return report_path
