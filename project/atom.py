#function auth check
import jwt,json
async def function_auth_check(request,jwt_token_decode,jwt_secret_key,root_secret_key,postgres_object):
  user=None
  path=request.url.path
  if "/root" in path:
    authorization_header=request.headers.get("Authorization")
    if not authorization_header:return {"status":0,"message":"authorization header missing"}
    token=authorization_header.split(" ",1)[1]
    if token!=root_secret_key:return {"status":0,"message":"token mismatch"}
  if "/my" in path:
    response=await jwt_token_decode(request,jwt_secret_key,None)
    if response["status"]==0:return response
    user=response["message"]
  if "/private" in path:
    response=await jwt_token_decode(request,jwt_secret_key,None)
    if response["status"]==0:return response
    user=response["message"]
  if "/admin" in path:
    response=await jwt_token_decode(request,jwt_secret_key,postgres_object)
    if response["status"]==0:return response
    user=response["message"]
    if user["is_active"]==0:return {"status":0,"message":"user not active"}
    if not user["api_access"]:return {"status":0,"message":"api access denied"}
    if path not in user["api_access"].split(","):return {"status":0,"message":"api access denied"}
  return {"status":1,"message":user}



#env
from environs import Env
env=Env()
env.read_env()
print("env loaded")

#sentry
import sentry_sdk
if False:
   sentry_sdk.init(dsn=env("sentry_dsn"),traces_sample_rate=1.0,profiles_sample_rate=1.0)
   print("sentry added")

#redis cache
from redis import asyncio as aioredis
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache
async def redis_cache_connect():
   redis_client=aioredis.from_url(env("redis_server_url"))
   FastAPICache.init(RedisBackend(redis_client))
   print("redis cache connected")
   return {"status":1,"message":"done"}

#redis rate limiter
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
from fastapi_cache.backends.redis import RedisBackend
async def redis_rate_limiter_connect():
   redis_client=aioredis.from_url(env("redis_server_url"),encoding="utf-8",decode_responses=True)
   await FastAPILimiter.init(redis_client)
   print("redis rate limiter connected")
   return {"status":1,"message":"done"}

#postgtes connect
postgres_client=None
from databases import Database
async def postgres_connect():
   global postgres_client
   postgres_client=Database(env("postgres_database_url"),min_size=1,max_size=100)
   await postgres_client.connect()
   print("postgres connected")
   return {"status":1,"message":"done"}

#postgtes disconnect
async def postgres_disconnect():
   await postgres_client.disconnect()
   print("postgres disconnected")
   return {"status":1,"message":"done"}

#postgres schema
postgres_column_data_type=None
async def postgres_schema():
   global postgres_column_data_type
   query="select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   output=await postgres_client.fetch_all(query=query,values={})
   postgres_column_data_type={item["column_name"]:item["data_type"] for item in output}
   print("postgres schema initialized")
   return {"status":1,"message":"done"}

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app:FastAPI):
   print("lifespan started")
   await redis_rate_limiter_connect()
   yield
   await FastAPILimiter.close()
   print("redis rate limiter disconnected")
   print("lifespan ended")
   
#app
from fastapi import FastAPI
app=FastAPI(title="atom",lifespan=lifespan)

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback,time
from function import function_auth_check,jwt_token_decode,postgres_log_create,postgres_object_create,middleware_error
@app.middleware("http")
async def middleware(request:Request,api_function):
   try:
      start=time.time()
      #auth check
      
      
      response=await function_auth_check(request,jwt_token_decode,jwt_secret_key,root_secret_key,postgres_object)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
      
      
      #request assign
      request.state.postgres_object=postgres_object
      request.state.user=user
      request.state.column_datatype=column_datatype
      request.state.app=app
      #api response
      response=await api_function(request)
      #end
      end=time.time()
      #log create
      if request.url.path not in ["/"] and request.method in ["POST","GET","PUT","DELETE"]:await postgres_log_create(postgres_object,postgres_object_create,column_datatype,request,user,(end-start)*1000)
   #exception
   except Exception as e:
      print(traceback.format_exc())
      response=await middleware_error(e.args)
      return JSONResponse(status_code=400,content=response)
   #final
   return response




#main
import asyncio
async def main():
   async with asyncio.TaskGroup() as task_group:
      await task_group.create_task(postgres_connect())
      task_group.create_task(postgres_schema())
      task_group.create_task(redis_cache_connect())

#script init
import asyncio
import uvicorn
if __name__=="__main__":
   try:
      asyncio.run(main())
      uvicorn.run(app,host="0.0.0.0",log_level="info")
   except KeyboardInterrupt:
      asyncio.run(postgres_disconnect())