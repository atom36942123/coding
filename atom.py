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

#postgres object create
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_create(table,object_list,mode):
   if not object_list:return {"status":0,"message":"object list empty"}
   if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
   column_to_insert_list=[*object_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   for index,object in enumerate(object_list):
      for k,v in object.items():
         if k in postgres_column_data_type:datatype=postgres_column_data_type[k]
         else:return {"status":0,"message":f"{k} column not in postgres_column_data_type"}
         if not v:object_list[index][k]=None
         if k in ["password","google_id"]:object_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if "int" in datatype:object_list[index][k]=int(v) if v else None
         if datatype in ["numeric"]:object_list[index][k]=round(float(v),3) if v else None
         if "time" in datatype:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["date"]:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["jsonb"]:object_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:object_list[index][k]=v.split(",") if v else None
   background=BackgroundTasks()
   output=None
   if mode=="background":
      if len(object_list)==1:background.add_task(await postgres_client.fetch_all(query=query,values=object_list[0]))
      else:background.add_task(await postgres_client.execute_many(query=query,values=object_list))
   else:
      if len(object_list)==1:output=await postgres_client.fetch_all(query=query,values=object_list[0])
      else:output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

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
import traceback,time,jwt,json,hashlib
object_list_log=[]
@app.middleware("http")
async def middleware(request:Request,api_function):
   try:
      #start
      start=time.time()
      user=None
      token=request.headers.get("Authorization").split(" ",1)[1] if request.headers.get("Authorization") else None
      api=request.url.path
      gate=api.split("/")[1]
      #gate check
      if gate not in ["","root","auth","my","private","public","admin"]:return JSONResponse(status_code=400,content={"status":0,"message":"path not allowed"})
      #auth check
      if gate=="root":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"}) 
         if hashlib.sha256(token.encode()).hexdigest()!="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3":return JSONResponse(status_code=400,content={"status":0,"message":"token mismatch"})
      if gate=="my":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,env("jwt_secret_key"),algorithms="HS256")["data"])
      if gate=="private":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,env("jwt_secret_key"),algorithms="HS256")["data"])
      if gate=="admin":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,env("jwt_secret_key"),algorithms="HS256")["data"])
         output=await postgres_client.fetch_all(query="select * from users where id=:id;",values={"id":user["id"]})
         user=output[0] if output else None
         if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user exist for token"})
         if user["is_active"]==0:return JSONResponse(status_code=400,content={"status":0,"message":"user not active"})
         if not user["api_access"]:return JSONResponse(status_code=400,content={"status":0,"message":"you are not admin"})
         if api not in user["api_access"].split(","):return {"status":0,"message":"api access denied"}
      #end
      request.state.user=user
      response=await api_function(request)
      end=time.time()
      #log create
      if request.url.path not in ["/"] and request.method in ["POST","GET","PUT","DELETE"]:
         global object_list_log
         object={"created_by_id":user["id"] if user else None,"api":api,"response_time_ms":(end-start)*1000}
         object_list_log.append(object)
         if len(object_list_log)>1:
            await postgres_object_create("log",object_list_log,"background")
            object_list_log=[]
   #exception
   except Exception as e:
      print(traceback.format_exc())
      error="".join(e.args)
      if "constraint_unique_likes" in error:error="already liked"
      if "constraint_unique_users" in error:error="user already exist"
      if "enough segments" in error:error="token issue"
      return JSONResponse(status_code=400,content={"status":0,"message":error})
   #final
   return response

#router
import os,glob
current_directory_path=os.path.dirname(os.path.realpath(__file__))
filepath_all_list=[item for item in glob.glob(f"{current_directory_path}/*.py")]
filename_all_list=[item.rsplit("/",1)[1].split(".")[0] for item in filepath_all_list]
filename_api_list=[item for item in filename_all_list if "api" in item]
router_list=[]
for item in filename_api_list:
   file_module=__import__(item)
   router_list.append(file_module.router)
for item in router_list:app.include_router(item)
print("router added")

#api=/
@app.get("/")
async def root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#api=/root/postgres-init
@app.post("/root/postgres-init")
async def root_postgres_init(request:Request):
   #logic
   body=await request.json()
   postgres_schema_extension=body["extension"]
   postgres_schema_table=body["table"]
   postgres_schema_column=body["column"]
   postgres_schema_notnull=body["notnull"]
   postgres_schema_unique=body["unique"]
   postgres_schema_index=body["index"]
   postgres_schema_bulk_delete_disable=body["bulk_delete_disable"]
   postgres_schema_query=body["query"]
   #extension
   for item in postgres_schema_extension:
      query=f"create extension if not exists {item}"
      query_param={}
      await postgres_object.fetch_all(query=query,values=query_param)
      
   #final
   return {"status":1,"message":"done"}


#postgres init
async def postgres_init(postgres_object,postgres_schema):
  #postgres_schema
  
 
  #table
  schema_table=await postgres_object.fetch_all(query="select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE';",values={})
  schema_table_name_list=[item["table_name"] for item in schema_table]
  for item in postgres_schema_table:
    if item not in schema_table_name_list:
      query=f"create table if not exists {item} (id bigint primary key generated always as identity not null,created_at timestamptz default now() not null,created_by_id bigint);"
      query_param={}
      await postgres_object.fetch_all(query=query,values=query_param)
  #column
  schema_column=await postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
  schema_column_table={f"{item['column_name']}_{item['table_name']}":item["data_type"] for item in schema_column}
  for k,v in postgres_schema_column.items():
    for item in v[1]:
      if f"{k}_{item}" not in schema_column_table:
        query=f"alter table {item} add column if not exists {k} {v[0]};"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param)
  #protected
  schema_rule=await postgres_object.fetch_all(query="select rulename from pg_rules;",values={})
  schema_rule_name_list=[item["rulename"] for item in schema_rule]
  schema_column=await postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
  for item in schema_column:
    if item["column_name"]=="is_protected":
      rule_name=f"rule_delete_disable_{item['table_name']}"
      if rule_name not in schema_rule_name_list:
        query=f"create or replace rule {rule_name} as on delete to {item['table_name']} where old.is_protected=1 do instead nothing;"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param)
  #notnull
  schema_column=await postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
  schema_column_table_nullable={f"{item['column_name']}_{item['table_name']}":item["is_nullable"] for item in schema_column}
  for k,v in postgres_schema_notnull.items():
    for item in v:
      if schema_column_table_nullable[f"{k}_{item}"]=="YES":
        query=f"alter table {item} alter column {k} set not null;"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param)
  #unique
  schema_constraint=await postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
  schema_constraint_name_list=[item["constraint_name"] for item in schema_constraint]
  for k,v in postgres_schema_unique.items():
    for item in v:
      constraint_name=f"constraint_unique_{k}_{item}".replace(',','_')
      if constraint_name not in schema_constraint_name_list:
        query=f"alter table {item} add constraint {constraint_name} unique ({k});"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param)
  #index
  schema_index=await postgres_object.fetch_all(query="select indexname from pg_indexes where schemaname='public';",values={})
  schema_index_name_list=[item["indexname"] for item in schema_index]
  for k,v in postgres_schema_index.items():
    for item in v[1]:
      index_name=f"index_{k}_{item}"
      if index_name not in schema_index_name_list:
        query=f"create index concurrently if not exists {index_name} on {item} using {v[0]} ({k});"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param) 
  #set updated at now
  schema_trigger=await postgres_object.fetch_all(query="select trigger_name from information_schema.triggers;",values={})
  schema_trigger_name_list=[item["trigger_name"] for item in schema_trigger]
  function_set_updated_at_now=await postgres_object.fetch_all(query="create or replace function function_set_updated_at_now() returns trigger as $$ begin new.updated_at= now(); return new; end; $$ language 'plpgsql';",values={})
  for item in schema_column:
    if item["column_name"]=="updated_at":
      trigger_name=f"trigger_set_updated_at_now_{item['table_name']}"
      if trigger_name not in schema_trigger_name_list:
        query=f"create or replace trigger {trigger_name} before update on {item['table_name']} for each row execute procedure function_set_updated_at_now();"
        query_param={}
        await postgres_object.fetch_all(query=query,values=query_param)
  #delete disable bulk
  function_delete_disable_bulk=await postgres_object.fetch_all(query="create or replace function function_delete_disable_bulk() returns trigger language plpgsql as $$declare n bigint := tg_argv[0]; begin if (select count(*) from deleted_rows) <= n is not true then raise exception 'cant delete more than % rows', n; end if; return old; end;$$;",values={})
  for k,v in postgres_schema_bulk_delete_disable.items():
    trigger_name=f"trigger_delete_disable_bulk_{k}"
    query=f"create or replace trigger {trigger_name} after delete on {k} referencing old table as deleted_rows for each statement execute procedure function_delete_disable_bulk({v});"
    query_param={}
    await postgres_object.fetch_all(query=query,values=query_param)
  #query
  schema_constraint=await postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
  schema_constraint_name_list=[item["constraint_name"] for item in schema_constraint]
  for k,v in postgres_schema_query.items():
    if "add constraint" in v and v.split()[5] in schema_constraint_name_list:continue
    await postgres_object.fetch_all(query=v,values={})
  #final
  return {"status":1,"message":"done"}

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