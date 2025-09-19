from datetime import datetime

class Expense:
    _expense_id = 0
    
    def __init__(self, amount:float, description:str, payer, cost_breakdown:dict):
        Expense._expense_id += 1
        self.id = Expense._expense_id
        self.amount = amount
        self.date = datetime.now()
        self.description = description
        self.payer = payer
        self.cost_breakdown = cost_breakdown
        

    
class RecurringExpense(Expense):
    def __init__(self, amount, description, payer, cost_breakdown, frequency:str, end_date:datetime):
        super().__init__(amount, description, payer, cost_breakdown)
        
        if frequency.lower() not in ['daily','monthly','yearly']:
            raise ValueError('Incorrect frequency entered. Please specify if recurring payment is daily, monthly or yearly!')
        
        self.frequency = frequency
        self.end_date = end_date
        
    
        
        
        