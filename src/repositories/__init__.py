"""Repositories package exporting database data-access classes."""

from src.repositories.account_repo import AccountRepository
from src.repositories.budget_repo import BudgetRepository
from src.repositories.category_repo import CategoryRepository
from src.repositories.goal_repo import SavingsGoalRepository
from src.repositories.investment_repo import InvestmentRepository
from src.repositories.loan_repo import LoanRepository
from src.repositories.recurring_repo import RecurringRepository
from src.repositories.transaction_repo import TransactionRepository

__all__ = [
    "AccountRepository",
    "CategoryRepository",
    "TransactionRepository",
    "BudgetRepository",
    "SavingsGoalRepository",
    "LoanRepository",
    "RecurringRepository",
    "InvestmentRepository",
]
