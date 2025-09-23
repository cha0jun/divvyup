from datetime import datetime
import bcrypt
import uuid

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
        
    
class User:
    user_id = 0
    users = {}
    sessions = {}

    def __init__(self, user_id, name, email, password):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password

    @classmethod
    def signUp(cls, name, email, password):
        if email in cls.users:
            return False
        cls.user_id += 1
        user = cls(cls.user_id, name, email, bcrypt.hashpw(password, bcrypt.gensalt()))
        cls.users[email] = user
        return True

    @classmethod
    def logIn(cls, email, password):
        user = cls.users.get(email)
        if user and bcrypt.checkpw(password, user.password):
            session_id = str(uuid.uuid4())
            cls.sessions[session_id] = email
            return True
        return False

    @classmethod
    def logOut(cls, session_id):
        if session_id in cls.sessions:
            del cls.sessions[session_id]
            return True
        return False
    

class Member:

    def __init__(self, isAdmin):
        self.member_id = str(uuid.uuid4())
        self.isAdmin = isAdmin

        

        
        