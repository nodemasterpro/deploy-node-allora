services:
  source:
    container_name: offchain_source
    build: ./adapter/api/source
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000"]
      interval: 10s
      timeout: 5s
      retries: 5
    network_mode: "host"     

  node:
    container_name: offchain_node
    build: .
    ports:
      - "2112:2112"
    volumes:
      - ./data:/data
    depends_on:
      source:
        condition: service_healthy
    env_file:
      - ./data/env_file 
    network_mode: "host"    
