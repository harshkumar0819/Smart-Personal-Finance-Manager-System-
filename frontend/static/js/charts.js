//  * FinWise - Chart.js Analytics Controller
//  * Initializes dashboard visual analytics dynamically from database attributes or sample preview data.
//  */

document.addEventListener('DOMContentLoaded', () => {
    const chartFont = {
        family: 'Inter, sans-serif',
        size: 11,
        weight: '500'
    };

    const chartText = '#73786F';
    const chartGrid = 'rgba(228, 227, 218, 0.75)';

    const cashFlowCtx = document.getElementById('cashFlowChart');

    if (cashFlowCtx) {
        let labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'];
        let incomeData = [72000, 75000, 80000, 78000, 82000, 85000];
        let expenseData = [41000, 39500, 44000, 36000, 42000, 38250];

        if (cashFlowCtx.dataset.labels) {
            try {
                labels = JSON.parse(cashFlowCtx.dataset.labels);
                incomeData = JSON.parse(cashFlowCtx.dataset.income || '[]');
                expenseData = JSON.parse(cashFlowCtx.dataset.expenses || '[]');
            } catch (e) {
                console.warn('FinWise: Using fallback chart data:', e);
            }
        }

        new Chart(cashFlowCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Income (₹)',
                        data: incomeData,
                        backgroundColor: '#71856B',
                        hoverBackgroundColor: '#5E7358',
                        borderRadius: 7,
                        borderSkipped: false,
                        maxBarThickness: 28
                    },
                    {
                        label: 'Expenses (₹)',
                        data: expenseData,
                        backgroundColor: '#C56D65',
                        hoverBackgroundColor: '#AD5B54',
                        borderRadius: 7,
                        borderSkipped: false,
                        maxBarThickness: 28
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'rectRounded',
                            boxWidth: 9,
                            boxHeight: 9,
                            padding: 18,
                            color: chartText,
                            font: chartFont
                        }
                    },
                    tooltip: {
                        backgroundColor: '#303A32',
                        titleColor: '#FFFFFF',
                        bodyColor: '#F7F7F2',
                        padding: 12,
                        cornerRadius: 9,
                        displayColors: true,
                        callbacks: {
                            label: (context) =>
                                ` ${context.dataset.label}: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            color: chartText,
                            font: chartFont
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: chartGrid,
                            drawTicks: false
                        },
                        border: {
                            display: false,
                            dash: [4, 4]
                        },
                        ticks: {
                            padding: 10,
                            color: chartText,
                            font: chartFont,
                            callback: (value) => {
                                if (value >= 1000) return '₹' + (value / 1000) + 'k';
                                return '₹' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    const categoryCtx = document.getElementById('categoryChart');

    if (categoryCtx) {
        let catLabels = [
            'Housing & Rent',
            'Groceries & Food',
            'Utilities & Bills',
            'Entertainment',
            'Transit & Fuel'
        ];

        let catData = [15000, 9500, 4250, 4500, 5000];

        const catColors = [
            '#71856B',
            '#A3B18A',
            '#C7B99B',
            '#8A9B9B',
            '#B18A50'
        ];

        if (categoryCtx.dataset.labels) {
            try {
                catLabels = JSON.parse(categoryCtx.dataset.labels);
                catData = JSON.parse(categoryCtx.dataset.values || '[]');
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
                    hoverBackgroundColor: [
                        '#5E7358',
                        '#899A70',
                        '#B7A787',
                        '#758989',
                        '#96733E'
                    ],
                    borderWidth: 3,
                    borderColor: '#FFFFFF',
                    hoverOffset: 7,
                    spacing: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 8,
                            boxHeight: 8,
                            padding: 14,
                            color: chartText,
                            font: {
                                family: 'Inter, sans-serif',
                                size: 10,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#303A32',
                        titleColor: '#FFFFFF',
                        bodyColor: '#F7F7F2',
                        padding: 12,
                        cornerRadius: 9,
                        callbacks: {
                            label: (context) =>
                                ` ${context.label}: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`
                        }
                    }
                }
            }
        });
    }
});
