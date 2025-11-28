-- -----------------------------------------------------------------------------
-- MySQL Schema
-- -----------------------------------------------------------------------------

-- It's good practice to set foreign key checks at the start and end of a script.
SET FOREIGN_KEY_CHECKS=0;

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
DROP TABLE IF EXISTS `payment`;
DROP TABLE IF EXISTS `platform_logs`;

SET FOREIGN_KEY_CHECKS=1;

-- -----------------------------------------------------------------------------
-- User Table
-- Stores user account information.
-- -----------------------------------------------------------------------------
CREATE TABLE `user` (
    `id` INT AUTO_INCREMENT PRIMARY KEY, -- CONVERSION NOTE: Changed from INTEGER PRIMARY KEY
    `name` VARCHAR(255) NOT NULL, -- CONVERSION NOTE: Changed from TEXT for better indexing and length constraint
    `email` VARCHAR(255) NOT NULL UNIQUE, -- CONVERSION NOTE: Changed from TEXT
    `password_hash` VARCHAR(255) NOT NULL, -- CONVERSION NOTE: Changed from TEXT as hashes have a fixed length
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- CONVERSION NOTE: Changed from TEXT to DATETIME
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- CONVERSION NOTE: Changed from TEXT and uses MySQL auto-update feature
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Expense Group Table
-- Stores groups for sharing expenses. Each group has an admin.
-- -----------------------------------------------------------------------------
CREATE TABLE `expense_group` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `admin_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `created_by` INT NOT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modified_by` INT NOT NULL,
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(`admin_id`) REFERENCES `user`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Member Table (Junction Table)
-- Links users to expense_groups, representing group membership (many-to-many).
-- -----------------------------------------------------------------------------
CREATE TABLE `member` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `expense_group_id` INT NOT NULL,
    `added_by` INT,
    `added_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    -- FIXED: Added ON DELETE SET NULL to prevent locking deletions
    FOREIGN KEY(`added_by`) REFERENCES `member`(`id`) ON DELETE SET NULL, 

    UNIQUE(`user_id`, `expense_group_id`)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Expense Table
-- Stores individual expense records within a group.
-- -----------------------------------------------------------------------------
CREATE TABLE `expense` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `expense_group_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL CHECK(`amount` > 0), 
    `payment_date` DATE NOT NULL,
    `payer_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `created_by` INT NOT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modified_by` INT NOT NULL,
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `receipt_path` TEXT, -- FIXED: Removed single quotes

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`payer_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- Recurring Expense Table
-- Stores recurrence details for an expense (one-to-one relationship).
-- -----------------------------------------------------------------------------
CREATE TABLE `recurring_expense` (
    `expense_id` INT PRIMARY KEY, -- This is both PK and FK
    `frequency` VARCHAR(50) NOT NULL, -- e.g., 'daily', 'weekly', 'monthly'
    `start_date` DATE NOT NULL,
    `end_date` DATE,
    `created_by` INT NOT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modified_by` INT NOT NULL,
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(`expense_id`) REFERENCES `expense`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Breakdown Table
-- Stores how an expense is split among users.
-- -----------------------------------------------------------------------------
CREATE TABLE `breakdown` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `expense_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL, -- CONVERSION NOTE: Changed from REAL to DECIMAL
    `debtor_id` INT NOT NULL,
    `created_by` INT NOT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modified_by` INT NOT NULL,
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(`expense_id`) REFERENCES `expense`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`debtor_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`),
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- Audit Table
-- Logs changes made within an expense group for transparency.
-- -----------------------------------------------------------------------------
CREATE TABLE `audit` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `change_description` TEXT NOT NULL,
    `expense_group_id` INT,
    `created_by` INT,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE SET NULL,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Invitation Table
-- Stores invitations for existing users to join an expense group.
-- -----------------------------------------------------------------------------
CREATE TABLE `invitation` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `expense_group_id` INT NOT NULL,
    `inviter_id` INT NOT NULL,
    `invitee_id` INT NOT NULL,
    `status` VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK(`status` IN ('pending', 'accepted', 'declined', 'canceled')),
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`inviter_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`invitee_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Token Blocklist Table
-- Stores revoked JWT (jti) identifiers until they expire.
-- -----------------------------------------------------------------------------
CREATE TABLE `token_blocklist` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `jti` VARCHAR(255) NOT NULL UNIQUE, -- The JWT unique ID (jti)
    `expiry_dt` DATETIME NOT NULL      -- When the token expires (for cleanup)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- Payment Table
-- Records payments made between members within a group to settle balances.
-- -----------------------------------------------------------------------------
CREATE TABLE `payment` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `expense_group_id` INT NOT NULL,
    `payer_id` INT NOT NULL,
    `payee_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL CHECK (`amount` > 0),
    `payment_date` DATE NOT NULL,
    `created_by` INT NOT NULL,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modified_by` INT NOT NULL,
    `modified_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(`expense_group_id`) REFERENCES `expense_group`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`payer_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`payee_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`created_by`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY(`modified_by`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `platform_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `description` TEXT NOT NULL,
    `performed_by` INT,
    `created_on` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(`performed_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Indexes
-- Create indexes on foreign keys to improve query performance.
-- (CONVERSION NOTE: This syntax is identical between SQLite and MySQL)
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
CREATE INDEX `idx_payment_group` ON `payment`(`expense_group_id`);
CREATE INDEX `idx_payment_payer` ON `payment`(`payer_id`);
CREATE INDEX `idx_payment_payee` ON `payment`(`payee_id`);
CREATE INDEX `idx_payment_date` ON `payment`(`payment_date`);


-- -----------------------------------------------------------------------------
-- Triggers
-- CONVERSION NOTE: The original SQLite triggers are no longer needed.
-- In MySQL, the 'modified_on' columns are defined with
-- `ON UPDATE CURRENT_TIMESTAMP`, which handles this functionality automatically
-- and more efficiently than a trigger.
-- -----------------------------------------------------------------------------