from datetime import datetime
import bcrypt
import uuid

class User:
    # class level attributes
    user_id = 0
    users = {}
    sessions = {}

    # instance level attributes
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
        # .get() <= dict method
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
   
    
class Expense:
    _expense_id = 0
    
    def __init__(self, amount:float, description:str, payer, cost_breakdown:dict, created_by: Member):
        Expense._expense_id += 1
        self.id = Expense._expense_id
        self.amount = amount
        self.date = datetime.now()
        self.description = description
        self.payer = payer
        self.cost_breakdown = cost_breakdown
        self.created_by = created_by

    # Setter methods
    def update_amount(self, new_amount: float):
        if new_amount <= 0:
            raise ValueError("Amount must be positive")
        self.amount = new_amount

    def update_description(self, new_description: str):
        self.description = new_description

    def update_payer(self, new_payer):
        self.payer = new_payer

    def update_cost_breakdown(self, new_breakdown: dict):
        self.cost_breakdown = new_breakdown
        
    
class RecurringExpense(Expense):
    def __init__(self, amount, description, payer, cost_breakdown, created_by, frequency:str, end_date:datetime):
        super().__init__(amount, description, payer, cost_breakdown, created_by)
        
        if frequency.lower() not in ['daily','monthly','yearly']:
            raise ValueError('Incorrect frequency entered. Please specify if recurring payment is daily, monthly or yearly!')
        
        self.frequency = frequency
        self.end_date = end_date

class ExpenseGroup:
    def __init__(self, group_id:int, group_name: str, description:str,createdBy: User):
        self.group_id = group_id
        self.group_name = group_name
        self.description = description
        self.createdBy = createdBy #user object
        self.members = []  #List of Member objects
        self.expenses = []
        self.audit_trail = []

    def is_member(self,member: Member):
        return member in self.members
    
    #validation helper methods
    def _require_member(self, member):
        # Validates that the member belongs to this group
        if member not in self.members:
            raise PermissionError("Access denied. You must be a member of this group to perform this action.")
        
    def _require_admin(self, member):
        # Validates that the member is both a group member and an admin
        self._require_member(member)
        if not member.is_admin:
            raise PermissionError("Only admins can perform this action.")
        
    def _require_creator_or_admin(self, member, expense):
        # Validates that the member is either the expense creator or an admin
        self._require_member(member)
        if not (member.is_admin or expense.created_by == member):
            raise PermissionError("Access denied. Non-admins can only manage their own expenses.")
        
    
    def add_member(self,performed_by: Member, new_user: User, is_admin= False):
        # Adds a user to the group if the performer is an admin
        self._require_admin(performed_by)

        for member in self.members:
            if member.user == new_user:
                # can consider to just break instead of throwing exception to let the method go through without adding. helps to also keep method idempotent - Matthew
                raise Exception("User is already a member of this group.")
     
        new_member = Member(new_user,is_admin) 
        self.members.append(new_member)

    
    def remove_member(self,performed_by: Member, member : Member):
        # Removes a member from the group if performer is an admin
        self._require_admin(performed_by)
        if member not in self.members:
            raise Exception ("User is not a member of this group.")
        
        self.members.remove(member)
        

    def update_member(self, performed_by: Member, target_member: Member):
        self._require_admin(performed_by)
        target_member.is_admin = True
        # missing logic to update member - Matthew
        
    def view_members(self):
        return f"Current member list: {self.members}" #Return member objects.
    #Member names will be added later after the Member and User classes are implemented

    def add_expense(
        self,
        current_member: Member,
        amount:float,
        description:str,
        payer, 
        cost_breakdown:dict,
        created_by: Member):

        self._require_member(current_member)
        self._require_member(payer)
        self._require_creator_or_admin(current_member)
        
        expense = Expense(amount, description,payer,cost_breakdown, created_by)
        self.expenses.append(expense)
        
        
    def update_expense(self, member, expense_id, **details):
        self._require_member(member)
        self._require_creator_or_admin(member, expense)
        
        expense = next((e for e in self.expenses if e.id == expense_id), None)
        if expense is None:
            raise ValueError(f"Expense with id: {expense_id} not found")
         
        if 'amount' in details :
            expense.update_amount(details['amount'])
        if 'description' in details:
            expense.update_description(details['description'])
        if 'payer' in details:
            expense.update_payer(details['payer'])
        if 'cost_breakdown' in details:
            expense.update_cost_breakdown(details['cost_breakdown'])
        

    def delete_expense(self,member:Member, expense, expense_id):
        self._require_member(member)
        self._require_creator_or_admin(member, expense)
        
        expense = next((e for e in self.expenses if e.id == expense_id), None)
        if expense is None:
            raise ValueError(f"Expense with id: {expense_id} not found")

        self.expenses.remove(expense)

    def view_expenses(self, member):
        self._require_member(member)

        if not self.expenses:
            return []
        
        expense_list = []
        for expense in self.expenses:
            expense_list.append({
                "id": expense.id,
                "description": expense.description,
                "amount": expense.amount,
                "date": expense.date.strftime("%Y-%m-%d %H:%M"),
                "payer": getattr(expense.payer, "name", str(expense.payer)),
                "created_by": getattr(expense.created_by, "name", str(expense.created_by)),
                "cost_breakdown": expense.cost_breakdown
            })
        return expense_list

    def calculate_balances():
        pass

    def view_audit_trail():
        pass


        

        
        