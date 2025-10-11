-- Enables foreign key constraint enforcement.
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Drop existing tables (in reverse order of creation)
-- This is useful for development to reset the database.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS recurring_expense;
DROP TABLE IF EXISTS breakdown;
DROP TABLE IF EXISTS debt;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS expense;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS expense_group;
DROP TABLE IF EXISTS "user"; -- "user" is a keyword, so it's safer to quote it.

-- -----------------------------------------------------------------------------
-- User Table
-- Stores user account information.
-- -----------------------------------------------------------------------------
CREATE TABLE "user" (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Expense Group Table
-- Stores groups for sharing expenses. Each group has an admin.
-- -----------------------------------------------------------------------------
CREATE TABLE expense_group (
    id INTEGER PRIMARY KEY,
    admin_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER NOT NULL,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(admin_id) REFERENCES "user"(id) ON DELETE RESTRICT, -- Don't delete a user if they are an admin
    FOREIGN KEY(created_by) REFERENCES "user"(id),
    FOREIGN KEY(modified_by) REFERENCES "user"(id)
);

-- -----------------------------------------------------------------------------
-- Member Table (Junction Table)
-- Links users to expense_groups, representing group membership (many-to-many).
-- -----------------------------------------------------------------------------
CREATE TABLE member (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expense_group_id INTEGER NOT NULL,
    added_by INTEGER NOT NULL,
    added_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY(expense_group_id) REFERENCES expense_group(id) ON DELETE CASCADE,
    FOREIGN KEY(added_by) REFERENCES "member"(id),

    -- Ensure a user can only join a group once.
    UNIQUE(user_id, expense_group_id)
);

-- -----------------------------------------------------------------------------
-- Expense Table
-- Stores individual expense records within a group.
-- -----------------------------------------------------------------------------
CREATE TABLE expense (
    id INTEGER PRIMARY KEY,
    expense_group_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date TEXT NOT NULL,
    payer_id INTEGER NOT NULL, -- Foreign key to the user table
    name TEXT NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER NOT NULL,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(expense_group_id) REFERENCES expense_group(id) ON DELETE CASCADE,
    FOREIGN KEY(payer_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES "user"(id),
    FOREIGN KEY(modified_by) REFERENCES "user"(id)
);

-- -----------------------------------------------------------------------------
-- Recurring Expense Table
-- Stores recurrence details for an expense (one-to-one relationship).
-- -----------------------------------------------------------------------------
CREATE TABLE recurring_expense (
    expense_id INTEGER PRIMARY KEY, -- This is both PK and FK
    frequency TEXT NOT NULL, -- e.g., 'daily', 'weekly', 'monthly'
    start_date TEXT NOT NULL,
    end_date TEXT,
    created_by INTEGER NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER NOT NULL,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(expense_id) REFERENCES expense(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES "user"(id),
    FOREIGN KEY(modified_by) REFERENCES "user"(id)
);

-- -----------------------------------------------------------------------------
-- Breakdown Table
-- Stores how an expense is split among users.
-- The sum of amounts here should equal the parent expense.amount.
-- -----------------------------------------------------------------------------
CREATE TABLE breakdown (
    id INTEGER PRIMARY KEY,
    expense_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    paid_by_id INTEGER NOT NULL, -- Foreign key to the user table
    created_by INTEGER NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER NOT NULL,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(expense_id) REFERENCES expense(id) ON DELETE CASCADE,
    FOREIGN KEY(paid_by_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES "user"(id),
    FOREIGN KEY(modified_by) REFERENCES "user"(id)
);

-- -----------------------------------------------------------------------------
-- Debt Table
-- Tracks calculated debts between members of a group.
-- -----------------------------------------------------------------------------
CREATE TABLE debt (
    id INTEGER PRIMARY KEY,
    expense_group_id INTEGER NOT NULL,
    creditor_id INTEGER NOT NULL, -- The user who is owed money
    debtor_id INTEGER NOT NULL,   -- The user who owes money
    amount REAL NOT NULL,
    created_by INTEGER NOT NULL,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER NOT NULL,
    modified_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(expense_group_id) REFERENCES expense_group(id) ON DELETE CASCADE,
    FOREIGN KEY(creditor_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY(debtor_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES "user"(id),
    FOREIGN KEY(modified_by) REFERENCES "user"(id)
);

-- -----------------------------------------------------------------------------
-- Audit Table
-- Logs changes made within an expense group for transparency.
-- -----------------------------------------------------------------------------
CREATE TABLE audit (
    id INTEGER PRIMARY KEY,
    change_description TEXT NOT NULL,
    expense_group_id INTEGER,
    created_by INTEGER,
    created_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(expense_group_id) REFERENCES expense_group(id) ON DELETE SET NULL,
    FOREIGN KEY(created_by) REFERENCES "user"(id) ON DELETE SET NULL -- audit records are retain despite parents rows being deleted
);


-- -----------------------------------------------------------------------------
-- Indexes
-- Create indexes on foreign keys to improve query performance.
-- -----------------------------------------------------------------------------
CREATE INDEX idx_group_admin ON expense_group(admin_id);
CREATE INDEX idx_member_user ON member(user_id);
CREATE INDEX idx_member_group ON member(expense_group_id);
CREATE INDEX idx_expense_group ON expense(expense_group_id);
CREATE INDEX idx_expense_payer ON expense(payer_id);
CREATE INDEX idx_breakdown_expense ON breakdown(expense_id);
CREATE INDEX idx_debt_group ON debt(expense_group_id);
CREATE INDEX idx_debt_creditor ON debt(creditor_id);
CREATE INDEX idx_debt_debtor ON debt(debtor_id);
CREATE INDEX idx_audit_group ON audit(expense_group_id);


-- -----------------------------------------------------------------------------
-- Triggers
-- Automatically update the 'modified_on' timestamp for relevant tables.
-- -----------------------------------------------------------------------------
CREATE TRIGGER update_user_modified_on
AFTER UPDATE ON "user"
FOR EACH ROW
BEGIN
    UPDATE "user" SET modified_on = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_expense_group_modified_on
AFTER UPDATE ON expense_group
FOR EACH ROW
BEGIN
    UPDATE expense_group SET modified_on = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_expense_modified_on
AFTER UPDATE ON expense
FOR EACH ROW
BEGIN
    UPDATE expense SET modified_on = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_recurring_expense_modified_on
AFTER UPDATE ON recurring_expense
FOR EACH ROW
BEGIN
    UPDATE recurring_expense SET modified_on = CURRENT_TIMESTAMP WHERE expense_id = OLD.expense_id;
END;

CREATE TRIGGER update_breakdown_modified_on
AFTER UPDATE ON breakdown
FOR EACH ROW
BEGIN
    UPDATE breakdown SET modified_on = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_debt_modified_on
AFTER UPDATE ON debt
FOR EACH ROW
BEGIN
    UPDATE debt SET modified_on = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;