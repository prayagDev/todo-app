from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import pymongo
from bson import ObjectId

app = FastAPI()
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
todo_db = myclient["todo_app"]
todo_col = todo_db["todo"]

class TodoSchema(BaseModel):
    subject: str
    description: str


@app.post("/")
async def todo(payload: TodoSchema):
    try:    
        mydict = { "subject": payload.subject, "description": payload.description, 
                  "status": "open" }

        x = todo_col.insert_one(mydict)

        print(x.inserted_id)

        return {}
    
    except Exception as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=str(e))
    

@app.get("/{id}")
async def todo(id: str):
    try:
        query = {"_id": ObjectId(id)}
        doc = todo_col.find_one(query, {"description": 1, "_id": 0})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Todo not found"
            )
        
        return doc

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )


@app.put("/{id}")
async def todo(id: str, payload: TodoSchema):
    try:
        print(id, type(id))
        query = {"_id": ObjectId(id), "status": "open"}
        mydict = { "subject": payload.subject, "description": payload.description}
        todo_col.update_one(
            query, 
            {'$set': mydict}
        )

        return {}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

@app.put("/complete/{id}")
async def complete(id: str):
    try:
        query = {"_id": ObjectId(id), "status": "open"}
        mydict = { "status": "complete"}
        todo_col.update_one(
            query, 
            {'$set': mydict}
        )

        return {}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )


@app.get("/")
async def todo(status: str = "open", page: int = 1, page_size: int = 10):
    query = {"status": status}
    projection = {"_id": 1, "subject": 1}
    skip_amount = (page - 1) * page_size
    cursor = todo_col.find(query, projection).skip(skip_amount).limit(page_size)
    docs = list(cursor)
    for doc in docs:
        doc['_id'] = str(doc['_id'])
    total_count = todo_col.count_documents(query)
    return {
        "records": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }

