docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/tmp/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant