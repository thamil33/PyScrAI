uvicorn pyscrai.databases.api.main: 
- start api server

DATABASE Scripts: 
  python -m pyscrai.scripts.init_db              # Interactive mode with menu

    python -m pyscrai.scripts.init_db --init       # Initialize without prompting

    python -m pyscrai.scripts.init_db --reset      # Reset without prompting (CAUTION!)
    
    python -m pyscrai.scripts.init_db --info       # Display database info only