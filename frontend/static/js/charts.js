/**
 * FinWise - Chart.js Analytics Controller
 * Initializes dashboard visual analytics dynamically from database attributes or sample preview data.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Cash Flow Bar/Line Chart (Monthly Income vs. Expense)
    const cashFlowCtx = document.getElementById('cashFlowChart');
    if (cashFlowCtx) {
        let labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'];
        let incomeData = [72000, 75000, 80000, 78000, 82000, 85000];
        let expenseData = [41000, 39500, 44000, 36000, 42000, 38250];

        // Parse dynamic live database data if available
        if (cashFlowCtx.dataset.labels) {
            try {
                labels = JSON.parse(cashFlowCtx.dataset.labels);
                incomeData = JSON.parse(cashFlowCtx.dataset.income || '[]');
                expenseData = JSON.parse(cashFlowCtx.dataset.expenses || '[]');
            } catch (e) {
                console.warn('FinWise: Using fallback chart data due to parsing error:', e);
            }
        }

        new Chart(cashFlowCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income (₹)',
                        data: incomeData,
                        backgroundColor: 'rgba(16, 185, 129, 0.85)', // Emerald
                        borderRadius: 6,
                        maxBarThickness: 28,
                    },
                    {
                        label: 'Expenses (₹)',
                        data: expenseData,
                        backgroundColor: 'rgba(244, 63, 94, 0.85)', // Rose
                        borderRadius: 6,
                        maxBarThickness: 28,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            font: { family: 'ui-sans-serif, system-ui', size: 12, weight: '500' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.dataset.label}: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        grid: { color: 'rgba(226, 232, 240, 0.6)' },
                        ticks: {
                            callback: (value) => {
                                if (value >= 1000) return '₹' + (value / 1000) + 'k';
                                return '₹' + value;
                            },
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }

    // 2. Category Expense Breakdown (Doughnut Chart)
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        let catLabels = ['Housing & Rent', 'Groceries & Food', 'Utilities & Bills', 'Entertainment', 'Transit & Fuel'];
        let catData = [15000, 9500, 4250, 4500, 5000];
        let catColors = ['#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#0ea5e9'];

        // Parse dynamic live database data if available
        if (categoryCtx.dataset.labels) {
            try {
                catLabels = JSON.parse(categoryCtx.dataset.labels);
                catData = JSON.parse(categoryCtx.dataset.values || '[]');
                if (categoryCtx.dataset.colors) {
                    catColors = JSON.parse(categoryCtx.dataset.colors);
                }
            } catch (e) {
                console.warn('FinWise: Using fallback category chart data:', e);
            }
        }

        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catData,
                    backgroundColor: catColors,
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            padding: 12,
                            font: { family: 'ui-sans-serif, system-ui', size: 11, weight: '500' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.label}: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`
                        }
                    }
                }
            }
        });
    }
});
