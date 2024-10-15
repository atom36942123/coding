#image pull=docker pull mongodb/mongodb-community-server:latest
#container run=docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest
#terminal=mongosh
#check count=db.users.countDocuments({})

#brew
# brew tap mongodb/brew
# brew update
# brew install mongodb-community@8.0
# brew services start mongodb-community@8.0
# brew services stop mongodb-community@8.0
# brew services info mongodb-community@8.0
# brew install --cask mongodb-compass

#fastapi
from fastapi import FastAPI
from fastapi import Request
app = FastAPI()
@app.get("/")
async def root(request:Request):
   return request.headers
    
#client
import motor.motor_asyncio
from bson import ObjectId
client=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db=client.test

#api
@app.post("/create-user")
async def create_user(request:Request):
   object=await request.json()
   output=await db.users.insert_one(object)
   return repr(output.inserted_id)
   
@app.get("/read-user")
async def read_user(request:Request,id:str):
   output=await db.users.find_one({"_id":ObjectId(id)})
   if output:output['_id']=str(output['_id'])
   return output

@app.put("/update-user")
async def update_user(request:Request,id:str):
   object=await request.json()
   output=await db.users.update_one({"_id":ObjectId(id)},{"$set":object})
   return output.modified_count
 
@app.delete("/delete-user")
async def delete_user(request:Request,id:str):
   output=await db.users.delete_one({"_id":ObjectId(id)})
   return output.deleted_count
   