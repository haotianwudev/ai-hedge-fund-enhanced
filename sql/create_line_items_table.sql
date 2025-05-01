-- Create table for storing line items data
CREATE TABLE IF NOT EXISTS line_items (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    report_period DATE NOT NULL,
    period VARCHAR(10) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    line_item_name VARCHAR(255) NOT NULL,
    line_item_value NUMERIC(25, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_line_items_ticker ON line_items(ticker);
CREATE INDEX IF NOT EXISTS idx_line_items_report_period ON line_items(report_period);
CREATE INDEX IF NOT EXISTS idx_line_items_line_item_name ON line_items(line_item_name);
CREATE INDEX IF NOT EXISTS idx_line_items_ticker_line_item_name ON line_items(ticker, line_item_name);
CREATE INDEX IF NOT EXISTS idx_line_items_ticker_report_period ON line_items(ticker, report_period);

-- Add comment to table
COMMENT ON TABLE line_items IS 'Stores financial line items data for companies';

-- Check if a unique constraint already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'line_items_ticker_report_period_period_line_item_name_key'
    ) THEN
        -- Add unique constraint
        ALTER TABLE line_items ADD CONSTRAINT line_items_ticker_report_period_period_line_item_name_key 
        UNIQUE (ticker, report_period, period, line_item_name);
    END IF;
EXCEPTION
    WHEN others THEN
        -- In case of error, just log and continue
        RAISE NOTICE 'Error creating unique constraint: %', SQLERRM;
END $$; 