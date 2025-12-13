from flask import Blueprint, render_template
from flask_login import login_required

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

def get_banks_data():
    return [
        {
            "name": "State Bank of India (SBI)",
            "type": "Solar Loan",
            "rating": 4.8,
            "details": "Surya Ghar Muft Bijli Yojana compatible. Interest rates starting from 7% p.a. for loans up to 3kW systems.",
            "link": "https://sbi.co.in/"
        },
        {
            "name": "Union Bank of India",
            "type": "Solar Loan",
            "rating": 4.6,
            "details": "Union Green Miles - Special rates for solar rooftop. Up to 100% financing available for installation costs.",
            "link": "https://www.unionbankofindia.co.in/"
        },
        {
            "name": "HDFC Bank",
            "type": "Green Credit Card",
            "rating": 4.5,
            "details": "5% cashback on solar equipment purchases. Convert large solar transactions into easy EMIs.",
            "link": "https://www.hdfcbank.com/"
        },
        {
            "name": "Canara Bank",
            "type": "Solar Loan",
            "rating": 4.3,
            "details": "Housing Loan for Solar. Low interest rates linked to RLLR. Repayment tenure up to 20 years.",
            "link": "https://canarabank.com/"
        },
        {
            "name": "ICICI Bank",
            "type": "EMI Scheme",
            "rating": 4.2,
            "details": "Flexible EMI options up to 60 months. No processing fee for select green energy partners.",
            "link": "https://www.icicibank.com/"
        },
        {
            "name": "Punjab National Bank",
            "type": "Solar Loan",
            "rating": 4.1,
            "details": "PNB Solar Scheme. Collateral-free loans for smaller systems. Quick processing.",
            "link": "https://www.pnbindia.in/"
        },
        {
            "name": "Axis Bank",
            "type": "Solar Loan",
            "rating": 4.0,
            "details": "Sustainable lending initiatives. Competitive rates for green housing projects including solar.",
            "link": "https://www.axisbank.com/"
        }
    ]

@finance_bp.route("/banks/", methods=["GET"])
@login_required
def banks():
    banks_data = get_banks_data()
    return render_template(
        "finance/banks.html",
        title="Financial Options",
        banks=banks_data
    )

