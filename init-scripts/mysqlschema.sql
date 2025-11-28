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
    `receipt_path` TEXT,

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
    `next_run_date` DATE,
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

DELIMITER $$

CREATE PROCEDURE `ProcessRecurringExpenses`()
BEGIN
    -- 1. Initialize next_run_date for new recurring setups
    UPDATE `recurring_expense`
    SET `next_run_date` = `start_date`
    WHERE `next_run_date` IS NULL;

    -- 2. Loop to handle "Catch-up" scenarios (e.g., if server was down)
    WHILE EXISTS (
        SELECT 1 FROM `recurring_expense` 
        WHERE `next_run_date` <= CURDATE() 
        AND (`end_date` IS NULL OR `next_run_date` <= `end_date`)
    ) DO

        -- A. Insert the new expense records based on the template
        INSERT INTO `expense` (
            `expense_group_id`,
            `amount`,
            `payment_date`,      -- Mapped to next_run_date
            `payer_id`,
            `name`,
            `description`,
            `created_by`,
            `created_on`,
            `modified_by`,
            `modified_on`,
            `receipt_path`       -- We set this to NULL for the new copy
        )
        SELECT 
            e.`expense_group_id`, -- Copy Group
            e.`amount`,           -- Copy Amount
            r.`next_run_date`,    -- **New Date** based on schedule
            e.`payer_id`,         -- Copy Payer
            e.`name`,             -- Copy Name
            e.`description`,      -- Copy Description
            r.`created_by`,       -- Assigned to the user who set up the schedule
            NOW(),                -- Created Now
            r.`modified_by`,      -- Assigned to the user who last modified schedule
            NOW(),                -- Modified Now
            NULL                  -- Receipt is NULL (waiting for user upload)
        FROM `recurring_expense` r
        JOIN `expense` e ON r.`expense_id` = e.`id`
        WHERE r.`next_run_date` <= CURDATE()
          AND (r.`end_date` IS NULL OR r.`next_run_date` <= r.`end_date`);

        -- B. Advance the schedule
        UPDATE `recurring_expense`
        SET `next_run_date` = CASE `frequency`
            WHEN 'daily'   THEN DATE_ADD(`next_run_date`, INTERVAL 1 DAY)
            WHEN 'weekly'  THEN DATE_ADD(`next_run_date`, INTERVAL 1 WEEK)
            WHEN 'monthly' THEN DATE_ADD(`next_run_date`, INTERVAL 1 MONTH)
            WHEN 'yearly'  THEN DATE_ADD(`next_run_date`, INTERVAL 1 YEAR)
            ELSE DATE_ADD(`next_run_date`, INTERVAL 1 MONTH)
        END,
        `modified_on` = NOW()
        WHERE `next_run_date` <= CURDATE()
          AND (`end_date` IS NULL OR `next_run_date` <= `end_date`);

    END WHILE;

END$$

DELIMITER ;

SET GLOBAL event_scheduler = ON;

CREATE EVENT `event_generate_recurring_expenses`
ON SCHEDULE EVERY 1 DAY
STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 1 DAY + INTERVAL 1 HOUR) -- Starts tomorrow at 01:00 AM
DO
    CALL `ProcessRecurringExpenses`();