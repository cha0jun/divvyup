from datetime import datetime
import bcrypt
import uuid

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

    def __init__(self,user: User, is_admin: bool = False):
        self.member_id = str(uuid.uuid4())
        self.user = user
        self.is_admin = is_admin
        self.owes = {} #track what this member owes to others {"memberid":amount_owned}
        #self.owes tracks TOTAL debts across ALL expenses in the group

    def add_debt(self, to_member_id: str, amount: float):
        """Add debt this member owes to another member"""
        self.owes[to_member_id] = self.owes.get(to_member_id,0) + amount

    def get_debt(self, to_member_id: str):
        """Get amount this member owes to specified member ID"""
        return self.owes.get(to_member_id, 0)
    
    def set_debt(self,to_member_id, amount):
        """Set debt amount to specified member ID"""
        self.owes[to_member_id] = amount
   
    
class Expense:
    _expense_id = 0
    
    def __init__(self, amount:float, description:str, payer, cost_breakdown:dict, created_by: Member):
        Expense._expense_id += 1
        self.id = Expense._expense_id
        self.amount = amount
        self.date = datetime.now()
        self.description = description
        self.payer = payer
        self.cost_breakdown = cost_breakdown #{member_id : amount_owned}
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
        #amount
 
    #validation helper methods
    def _require_member(self, member):
        """Validates that the member belongs to this group"""
        if member not in self.members:
            raise PermissionError("Access denied. You must be a member of this group to perform this action.")
        
    def _require_admin(self, member):
        """Validates that the member is both a group member and an admin"""
        self._require_member(member)
        if not member.is_admin:
            raise PermissionError("Only admins can perform this action.")
        
    def _require_creator_or_admin(self, member, expense):
        """Validates that the member is either the expense creator or an admin"""
        self._require_member(member)
        if not (member.is_admin or expense.created_by == member):
            raise PermissionError("Access denied. Non-admins can only manage their own expenses.")
        
    #helper methods

    def get_member(self,member_id):
        for member in self.members:
            if member.member_id == member_id:
                return member
            
    def _find_expense(self,expense_id):
        """Finds and returns an expense by ID, raises ValueError if not found"""
        expense = next((e for e in self.expenses if e.id == expense_id),None)
        if expense is None:
            raise ValueError(f"Expense with id: {expense_id} not found")
        return expense
    
    def _update_balances_for_expense(self, expense: Expense):
        """Apply balance changes for an expense.
           Returns a message describing what happened.
        """
        results =[]
        for member_id,owed_amount in expense.cost_breakdown.items():
            member = self.get_member(member_id)

            if member is None:
                raise ValueError(f"Unknown member id in breakdown: {member_id}")
            
            if member_id == expense.payer.member_id:
                results.append(f"{member.user.name} owes nobody for {expense.description}")
                
            else:
                member.add_debt(expense.payer.member_id,owed_amount)
                results.append(f"{member.user.name} owes {expense.payer.user.name} ${owed_amount:.2f} for {expense.description}")
        return results
    

    def _reverse_balances_for_expense(self, old_payer: Member, old_breakdown: dict):
        """Reverse debt effects of an expense (before updating/deleting it).
           Returns a list of results describing what was reversed.
        """
        results = []

        for member_id, owed_amount in old_breakdown.items():
            member = self.get_member(member_id)
            if member and member != old_payer:
                current_debt = member.get_debt(old_payer.member_id)
                new_debt = current_debt - owed_amount
                member.set_debt(old_payer.member_id, new_debt)

                results.append({"message": f"Reversed ${owed_amount:.2f} from {member.user.name}'s debt to {old_payer.user.name}"})

        return results
    

    #-------Member Management Methods---------
    def add_member(self,performed_by: Member, new_user: User, is_admin= False):
        """Adds a user to the group if the performer is an admin"""
        self._require_admin(performed_by)

        for member in self.members:
            if member.user == new_user: 
                raise Exception("User is already a member of this group.")
     
        new_member = Member(new_user,is_admin) 
        self.members.append(new_member)

        return new_member

    
    def remove_member(self,performed_by: Member, member : Member):
        """Removes a member from the group if performer is an admin"""
        self._require_admin(performed_by)
        if member not in self.members:
            raise Exception ("User is not a member of this group.")
        
        self.members.remove(member)
        return member
        

    def update_member (self, performed_by: Member, member: Member):
        self._require_admin(performed_by)
        member.is_admin = True

        return member
        
    def view_members(self):
        member_list = ", ".join(member.user.name for member in self.members)
        return f"Current member list: {member_list}" 
 
    #-------Expense Management Methods---------
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
        for user in cost_breakdown.keys():
            self._require_member(user)
        
        total_breakdown = sum(cost_breakdown.values())
        
        if abs(total_breakdown - amount) > 0.01: 
            raise ValueError("Cost breakdown doesn't match total expense amount")
        
        expense = Expense(amount, description,payer,cost_breakdown, created_by)
        self.expenses.append(expense)

        #update member balances
        self._update_balances_for_expense(expense)

        return expense
    
  
    def update_expense(self, member, expense_id, **details):
        """Update an expense if the member is either the expense creator or an admin"""
        expense = self._find_expense(expense_id)
        self._require_creator_or_admin(member, expense)

        #store old values
        old_payer = expense.payer
        old_breakdown = expense.cost_breakdown.copy()
        
        #update expense object
        if 'amount' in details :
            expense.update_amount(details['amount'])
        if 'description' in details:
            expense.update_description(details['description'])
        if 'payer' in details:
            self._require_member(details['payer'])
            expense.update_payer(details['payer'])
        if 'cost_breakdown' in details:
            expense.update_cost_breakdown(details['cost_breakdown'])

        #remove old balance effects
        self._reverse_balances_for_expense(old_payer, old_breakdown)

        #update new balance effects
        self._update_balances_for_expense(expense)

        return expense
        

    def delete_expense(self,member:Member, expense_id):
        """Delete an expense if the member is either the expense creator or an admin"""
        expense = self._find_expense(expense_id)
        self._require_creator_or_admin(member, expense)

       #reverse old expense for balance calculation
        self._reverse_balances_for_expense(expense.payer, expense.cost_breakdown)
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
                "payer": expense.payer.user.name,
                "created_by": expense.created_by.user.name,
                "cost_breakdown": expense.cost_breakdown
            })
        return expense_list
    

    #-------Balance Related Methods---------
    def offset_debts(self):
        """ Off set mutual debts between every pair of members (in-place)."""
        for i, memberA in enumerate(self.members):
            for memberB in self.members[i+1:]:
                memberA_owes =memberA.get_debt(memberB.member_id) 
                memberB_owes = memberB.get_debt(memberA.member_id)
                mutual_debt = min(memberA_owes,memberB_owes)
                if mutual_debt > 0:
                    memberA.set_debt(memberB.member_id, memberA_owes - mutual_debt)
                    memberB.set_debt(memberA.member_id, memberB_owes - mutual_debt)


    def get_balances(self, member: Member):
        self._require_member(member)
        self.offset_debts()
        all_balances = {}
        for group_member in self.members:
            owes_to = {} #record the amount group_member owes to others.
            owed_by ={} #record the amounts other members owe this member.
            for other_member in self.members:
                if group_member != other_member:
                    debt_group_member = group_member.get_debt(other_member.member_id)
                    if debt_group_member > 0:
                        owes_to[other_member.user.name] = f"${debt_group_member:.2f}"
                    
                    debt_other_member = other_member.get_debt(group_member.member_id)
                    if debt_other_member > 0:
                        owed_by[other_member.user.name] = f"${debt_other_member:.2f}"
            all_balances[group_member.user.name] = {
                                                    "owes to": owes_to,
                                                    "owed_by": owed_by
                                                    }
        return all_balances

    #-------Audit Methods---------
    def view_audit_trail():
        pass


        