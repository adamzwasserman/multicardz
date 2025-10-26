/**
 * Turso Browser Database Service
 * Provides local-first database using Turso WASM
 */

let dbInitialized = false;
let dbInstance = null;

/**
 * Initialize browser database with Turso WASM
 * Lazy loads WASM only when needed (privacy mode)
 */
export async function initializeBrowserDatabase() {
    if (dbInitialized) {
        console.log('✅ Browser database already initialized');
        return dbInstance;
    }

    try {
        console.log('🚀 Initializing Turso WASM browser database...');

        // Lazy load WASM (only loads when this function is called)
        const { connect } = await import('@tursodatabase/database-wasm');

        // Create local database in OPFS (Origin Private File System)
        // For browser, use ':memory:' or a local file name
        dbInstance = await connect('multicardz_local.db');

        console.log('✅ Browser database initialized successfully');
        console.log('Storage: Local file (OPFS in browser)');
        dbInitialized = true;

        return dbInstance;
    } catch (error) {
        console.error('❌ Failed to initialize browser database:', error);
        throw error;
    }
}

/**
 * Execute a query on the browser database
 */
export async function executeQuery(sql, params = []) {
    if (!dbInstance) {
        throw new Error('Database not initialized. Call initializeBrowserDatabase() first.');
    }

    try {
        // Use prepare().all() pattern for SELECT queries
        if (sql.trim().toUpperCase().startsWith('SELECT')) {
            const stmt = dbInstance.prepare(sql);
            const rows = await stmt.all(...params);
            return {
                success: true,
                rows: rows,
                rowsAffected: 0
            };
        }
        // Use exec() for DDL (CREATE, ALTER, DROP)
        else if (sql.trim().toUpperCase().match(/^(CREATE|ALTER|DROP)/)) {
            await dbInstance.exec(sql);
            return {
                success: true,
                rows: [],
                rowsAffected: 0
            };
        }
        // Use prepare().run() for INSERT, UPDATE, DELETE
        else {
            const stmt = dbInstance.prepare(sql);
            const result = await stmt.run(...params);
            return {
                success: true,
                rows: [],
                rowsAffected: result.changes || 0,
                lastInsertRowid: result.lastInsertRowid
            };
        }
    } catch (error) {
        console.error('❌ Query failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Execute multiple statements in a transaction
 */
export async function executeTransaction(statements) {
    if (!dbInstance) {
        throw new Error('Database not initialized. Call initializeBrowserDatabase() first.');
    }

    try {
        await dbInstance.batch(
            statements.map(({ sql, params }) => ({
                sql,
                args: params || []
            }))
        );
        
        return { success: true };
    } catch (error) {
        console.error('❌ Transaction failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Get database statistics
 */
export async function getDatabaseStats() {
    if (!dbInstance) {
        return {
            initialized: false,
            storage: 'none'
        };
    }

    try {
        // Get list of tables
        const tables = await executeQuery(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        );

        const stats = {
            initialized: true,
            storage: 'opfs',
            tables: tables.rows?.map(t => t.name) || []
        };

        // Count rows for each table
        for (const tableName of stats.tables) {
            try {
                const count = await executeQuery(`SELECT COUNT(*) as count FROM ${tableName}`);
                stats[tableName] = count.rows?.[0]?.count || 0;
            } catch (err) {
                stats[tableName] = `Error: ${err.message}`;
            }
        }

        return stats;
    } catch (error) {
        return {
            initialized: true,
            storage: 'opfs',
            error: error.message
        };
    }
}
