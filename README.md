# DBF to SQL API

Real-time ERP data pipeline that monitors DBF files and exposes data via FastAPI endpoints.

## Architecture

- **DBF Monitoring**: Watches for file changes using checksums for delta detection
- **MySQL Database**: Stores customer, product, and movement data
- **FastAPI**: REST API with automatic OpenAPI documentation
- **Docker**: Containerized deployment with external MySQL volume

## Features

- ✅ Real-time DBF file monitoring
- ✅ Delta detection using CRC32 checksums
- ✅ FoxPro memo file support (.FPT)
- ✅ MySQL database with proper indexing
- ✅ REST API with filtering and pagination
- ✅ External MySQL volume for data persistence
- ✅ Comprehensive logging and error handling

## Quick Start on Ubuntu Server

### 1. Prerequisites
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose cifs-utils

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### 2. Mount Windows Share
```bash
# Create mount point
sudo mkdir -p /mnt/dbf-share

# Add to /etc/fstab for persistent mounting
echo "//192.168.1.100/SAIT /mnt/dbf-share cifs username=anonymous,password=,uid=1000,gid=1000,iocharset=utf8,file_mode=0444,dir_mode=0555,ro 0 0" | sudo tee -a /etc/fstab

# Mount the share
sudo mount -a

# Verify
ls -la /mnt/dbf-share/
```

### 3. Deploy Application
```bash
# Clone repository
git clone <your-repo-url>
cd dbf_to_sql

# Create external MySQL volume (run once)
docker volume create mysql-shared-data

# Start services
docker-compose up --build -d

# Check status
docker-compose ps
docker-compose logs -f api
```

### 4. Access API
- **API Documentation**: http://your-server:8000/docs
- **Health Check**: http://your-server:8000/health
- **Customers**: http://your-server:8000/customers
- **Products**: http://your-server:8000/products  
- **Movements**: http://your-server:8000/movements

## API Endpoints

### Health & Status
- `GET /` - Basic health check
- `GET /health` - Detailed health with record counts
- `GET /status/files` - DBF file processing status
- `GET /status/sync-log` - Recent sync operations

### Customers
- `GET /customers` - List customers (with filtering)
- `GET /customers/{numcli}` - Get specific customer

### Products  
- `GET /products` - List products (with filtering)
- `GET /products/{numart}` - Get specific product

### Movements
- `GET /movements` - List movements (with filtering)
- `GET /movements/document/{tipodoc}/{numdoc}` - Get document movements

### Analytics
- `GET /analytics/sales-summary` - Sales summary data

## Configuration

Environment variables in `.env`:

```bash
# Database
MYSQL_ROOT_PASSWORD=rootpass123
MYSQL_DATABASE=sales_db
MYSQL_USER=sales_user
MYSQL_PASSWORD=sales_pass

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# DBF Files
DBF_WATCH_PATH=/app/data

# Logging
LOG_LEVEL=INFO
```

## Data Flow

1. **File Monitoring**: Watchdog monitors `/mnt/dbf-share` for DBF changes
2. **Delta Detection**: CRC32 checksums detect inserted/updated/deleted records
3. **Database Sync**: Changes are applied to MySQL using upsert operations
4. **API Access**: FastAPI exposes data with filtering, pagination, and analytics

## Database Schema

### Tables
- `customers` - Customer data from clientes.DBF
- `products` - Product catalog from arts.DBF  
- `movements` - Transaction data from Movim.DBF
- `dbf_file_state` - File processing tracking
- `sync_log` - Operation audit trail

### Key Features
- Foreign key relationships
- Proper indexing for performance
- Timestamp tracking (created_at, updated_at)
- Text fields for memo data

## Power BI Integration

Connect Power BI to MySQL:
1. Use MySQL connector in Power BI Desktop
2. Server: `your-ubuntu-server:3306`
3. Database: `sales_db`
4. Username: `sales_user`
5. Password: `sales_pass`

Features:
- Native MySQL connector
- Incremental refresh support
- Query folding optimization
- Direct query mode available

## Monitoring & Troubleshooting

### View Logs
```bash
# API logs
docker-compose logs -f api

# MySQL logs  
docker-compose logs -f mysql

# All logs
docker-compose logs -f
```

### Check File Processing
```bash
# View processing status
curl http://localhost:8000/status/files

# View sync log
curl http://localhost:8000/status/sync-log

# Health check
curl http://localhost:8000/health
```

### Common Issues

**DBF files not detected:**
- Check mount: `ls -la /mnt/dbf-share/`
- Verify container can see files: `docker exec dbf-api ls -la /app/data/`

**Database connection failed:**
- Check MySQL is running: `docker-compose ps`
- Verify network: `docker network ls`

**API not responding:**
- Check container logs: `docker-compose logs api`
- Verify port mapping: `docker-compose ps`

## Development

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run locally (with MySQL running)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Connect to MySQL
docker exec -it dbf-mysql mysql -u sales_user -p sales_db

# Backup database
docker exec dbf-mysql mysqldump -u root -p sales_db > backup.sql

# Restore database
docker exec -i dbf-mysql mysql -u root -p sales_db < backup.sql
```

## File Structure

```
dbf_to_sql/
├── docker-compose.yml          # Docker services
├── Dockerfile                  # API container
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── src/                       # Application source
│   ├── main.py               # FastAPI application
│   ├── config.py             # Configuration
│   ├── database.py           # Database connection
│   ├── models.py             # SQLAlchemy models
│   ├── api/                  # API layer
│   │   └── schemas.py        # Pydantic schemas
│   ├── dbf/                  # DBF processing
│   │   ├── reader.py         # DBF file reader
│   │   ├── watcher.py        # File monitoring
│   │   ├── sync.py           # Database sync
│   │   └── delta.py          # Change detection
│   └── utils/                # Utilities
│       └── logging.py        # Logging setup
├── sql/                      # Database schema
│   └── init.sql             # Initial schema
└── logs/                    # Application logs
```

## License

MIT License - see LICENSE file for details.