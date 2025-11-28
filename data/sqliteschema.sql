-- -----------------------------------------------------------------------------
-- SQLite Schema
-- -----------------------------------------------------------------------------

-- It's good practice to set foreign key checks at the start and end of a script.
PRAGMA foreign_keys = OFF;

-- -----------------------------------------------------------------------------
-- Drop existing tables (in reverse order of creation)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `token_blocklist`;
DROP TABLE IF EXISTS `invitation`;
DROP TABLE IF EXISTS `recurring_expense`;
DROP TABLE IF EXISTS `breakdown`;
DROP TABLE IF EXISTS `audit`;
DROP TABLE IF EXISTS `expense`;
DROP TABLE IF EXISTS `member`;
DROP TABLE IF EXISTS `expense_group`;
DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `platform_logs`;

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- User Table
-- Stores user account information.
-- -----------------------------------------------------------------------------
CREATE TABLE `user` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT NOT NULL,
    `email` TEXT NOT NULL UNIQUE,
    `password_hash` TEXT NOT NULL,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `modified_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW'))
);

-- -----------------------------------------------------------------------------
-- Expense Group Table
-- Stores groups for sharing expenses. Each group has an admin.
-- -----------------------------------------------------------------------------
CREATE TABLE `expense_group` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `admin_id` INTEGER NOT NULL,
    `name` TEXT NOT NULL,
    `description` TEXT,
    `created_by` INTEGER NOT NULL,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `modified_by` INTEGER NOT NULL,
    `modified_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`admin_id`) REFERENCES `user`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
);

-- -----------------------------------------------------------------------------
-- Member Table (Junction Table)
-- Links users to expense_groups, representing group membership (many-to-many).
-- -----------------------------------------------------------------------------
CREATE TABLE `member` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `user_id` INTEGER NOT NULL,
    `expense_group_id` INTEGER NOT NULL,
    `added_by` INTEGER,
    `added_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`added_by`) REFERENCES `member`(`id`),

    -- Ensure a user can only join a group once.
    UNIQUE(`user_id`, `expense_group_id`)
);

-- -----------------------------------------------------------------------------
-- Expense Table
-- Stores individual expense records within a group.
-- -----------------------------------------------------------------------------
CREATE TABLE `expense` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `expense_group_id` INTEGER NOT NULL,
    `amount` REAL NOT NULL CHECK(`amount` > 0), -- SQLite uses REAL for floating point numbers
    `payment_date` TEXT NOT NULL, -- Stored as TEXT in 'YYYY-MM-DD' format
    `payer_id` INTEGER NOT NULL,
    `name` TEXT NOT NULL,
    `description` TEXT,
    `created_by` INTEGER NOT NULL,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `modified_by` INTEGER NOT NULL,
    `modified_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `receipt_path` TEXT,

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`payer_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
);

-- -----------------------------------------------------------------------------
-- Recurring Expense Table
-- Stores recurrence details for an expense (one-to-one relationship).
-- -----------------------------------------------------------------------------
CREATE TABLE `recurring_expense` (
    `expense_id` INTEGER PRIMARY KEY, -- This is both PK and FK
    `frequency` TEXT NOT NULL, -- e.g., 'daily', 'weekly', 'monthly'
    `start_date` TEXT NOT NULL,
    `next_run_date` TEXT, -- Stored as TEXT in 'YYYY-MM-DD' format
    `end_date` TEXT, -- Stored as TEXT in 'YYYY-MM-DD' format
    `created_by` INTEGER NOT NULL,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `modified_by` INTEGER NOT NULL,
    `modified_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`expense_id`) REFERENCES `expense`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
);

-- -----------------------------------------------------------------------------
-- Breakdown Table
-- Stores how an expense is split among users.
-- -----------------------------------------------------------------------------
CREATE TABLE `breakdown` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `expense_id` INTEGER NOT NULL,
    `amount` REAL NOT NULL, -- SQLite uses REAL for floating point numbers
    `debtor_id` INTEGER NOT NULL,
    `created_by` INTEGER NOT NULL,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),
    `modified_by` INTEGER NOT NULL,
    `modified_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`expense_id`) REFERENCES `expense`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`debtor_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
);


-- -----------------------------------------------------------------------------
-- Audit Table
-- Logs changes made within an expense group for transparency.
-- -----------------------------------------------------------------------------
CREATE TABLE `audit` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `change_description` TEXT NOT NULL,
    `expense_group_id` INTEGER,
    `created_by` INTEGER,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE SET NULL,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- Invitation Table
-- Stores invitations for existing users to join an expense group.
-- -----------------------------------------------------------------------------
CREATE TABLE `invitation` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `expense_group_id` INTEGER NOT NULL,
    `inviter_id` INTEGER NOT NULL,
    `invitee_id` INTEGER NOT NULL,
    `status` TEXT NOT NULL DEFAULT 'pending' CHECK(`status` IN ('pending', 'accepted', 'declined', 'canceled')),
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`inviter_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`invitee_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- Token Blocklist Table
-- Stores revoked JWT (jti) identifiers until they expire.
-- -----------------------------------------------------------------------------
CREATE TABLE `token_blocklist` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `jti` TEXT NOT NULL UNIQUE, -- The JWT unique ID (jti)
    `expiry_dt` TEXT NOT NULL      -- When the token expires (for cleanup), stored as TEXT
);

CREATE TABLE `platform_logs` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `description` TEXT NOT NULL,
    `performed_by` INTEGER,
    `created_on` TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW')),

    FOREIGN KEY(`performed_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- Indexes
-- Create indexes on foreign keys to improve query performance.
-- -----------------------------------------------------------------------------
CREATE INDEX `idx_group_admin` ON `expense_group`(`admin_id`);
CREATE INDEX `idx_member_user` ON `member`(`user_id`);
CREATE INDEX `idx_member_group` ON `member`(`expense_group_id`);
CREATE INDEX `idx_expense_group` ON `expense`(`expense_group_id`);
CREATE INDEX `idx_expense_payer` ON `expense`(`payer_id`);
CREATE INDEX `idx_breakdown_expense` ON `breakdown`(`expense_id`);
CREATE INDEX `idx_audit_group` ON `audit`(`expense_group_id`);
CREATE INDEX `idx_invitation_group` ON `invitation`(`expense_group_id`);
CREATE INDEX `idx_invitation_inviter` ON `invitation`(`inviter_id`);
CREATE INDEX `idx_invitation_invitee` ON `invitation`(`invitee_id`);
CREATE INDEX `idx_blocklist_expires` ON `token_blocklist`(`expiry_dt`);


-- -----------------------------------------------------------------------------
-- Triggers for automatic `modified_on` updates in SQLite
-- -----------------------------------------------------------------------------

CREATE TRIGGER update_user_modified_on
AFTER UPDATE ON `user`
FOR EACH ROW
BEGIN
    UPDATE `user` SET `modified_on` = STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW') WHERE id = OLD.id;
END;

CREATE TRIGGER update_expense_group_modified_on
AFTER UPDATE ON `expense_group`
FOR EACH ROW
BEGIN
    UPDATE `expense_group` SET `modified_on` = STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW') WHERE id = OLD.id;
END;

CREATE TRIGGER update_expense_modified_on
AFTER UPDATE ON `expense`
FOR EACH ROW
BEGIN
    UPDATE `expense` SET `modified_on` = STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW') WHERE id = OLD.id;
END;

CREATE TRIGGER update_recurring_expense_modified_on
AFTER UPDATE ON `recurring_expense`
FOR EACH ROW
BEGIN
    UPDATE `recurring_expense` SET `modified_on` = STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW') WHERE expense_id = OLD.expense_id;
END;

CREATE TRIGGER update_breakdown_modified_on
AFTER UPDATE ON `breakdown`
FOR EACH ROW
BEGIN
    UPDATE `breakdown` SET `modified_on` = STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW') WHERE id = OLD.id;
END;