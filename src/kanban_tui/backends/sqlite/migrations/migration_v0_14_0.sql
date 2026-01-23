-- Migration v0.14.0: Add metadata field to tasks table
-- This adds support for backend-specific metadata storage

PRAGMA foreign_keys = OFF;

-- Add metadata column to tasks table with default empty JSON object
ALTER TABLE tasks ADD COLUMN metadata TEXT DEFAULT '{}';

PRAGMA foreign_keys = ON;
