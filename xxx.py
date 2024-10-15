
#root/postgres-qrunner
from fastapi import Request
from fastapi.responses import JSONResponse
@app.get("/root/postgres-qrunner")
async def root_postgres_qrunner(request:Request,query:str,mode:str=None):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  #logic
  if not mode:output=await postgres_object.fetch_all(query=query,values={})
  if mode=="bulk":output=[await postgres_object.fetch_all(query=item,values={}) for item in query.split("---")]
  #final
  return {"status":1,"message":output}

#root/grant-all-api-access
from fastapi import Request
@app.put("/root/grant-all-api-access")
async def root_grant_all_api_access(request:Request,user_id:int):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  app=request.state.app
  #logic
  api_admin_list=[route.path for route in app.routes if "/admin" in route.path]
  api_admin_str=",".join(api_admin_list)
  query="update users set api_access=:api_access where id=:id returning *"
  query_param={"api_access":api_admin_str,"id":user_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  #final
  return {"status":1,"message":output}

#auth/signup
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
@app.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def auth_signup(request:Request,username:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":{"user":user,"token":token}}

#auth/login
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
@app.get("/auth/login")
async def auth_login(request:Request,username:str,password:str,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="admin" and not user["api_access"]:return JSONResponse(status_code=400,content={"status":0,"message":"you are not admin"})
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#auth/login google
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
@app.get("/auth/login-google")
async def auth_login_google(request:Request,google_id:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"select * from users where google_id=:google_id order by id desc limit 1;"
   query_param={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:
     query=f"insert into users (google_id) values (:google_id) returning *;"
     query_param={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user=output[0]
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#auth/login email otp
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
from function import postgtes_otp_verify
@app.get("/auth/login-email-otp")
async def auth_login_email_otp(request:Request,email:str,otp:int,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #otp verify
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   query=f"select * from users where email=:email order by id desc limit 1;"
   query_param={"email":email}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if mode=="exist" and not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if not user:
     query=f"insert into users (email) values (:email) returning *;"
     query_param={"email":email}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user=output[0]
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#auth/login mobile otp
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
from function import postgtes_otp_verify
@app.get("/auth/login-mobile-otp")
async def auth_login_mobile_otp(request:Request,mobile:str,otp:int,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #otp verify
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   query=f"select * from users where mobile=:mobile order by id desc limit 1;"
   query_param={"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if mode=="exist" and not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if not user:
     query=f"insert into users (mobile) values (:mobile) returning *;"
     query_param={"mobile":mobile}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_object.fetch_all(query=query,values=query_param)
     user=output[0]
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#auth/login email password
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
@app.get("/auth/login-email-password")
async def auth_login_email_password(request:Request,email:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"select * from users where email=:email and password=:password order by id desc limit 1;"
   query_param={"email":email,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#auth/login mobile password
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import jwt_token_encode
from config import jwt_secret_key
@app.get("/auth/login-mobile-password")
async def auth_login_mobile_password(request:Request,mobile:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"select * from users where mobile=:mobile and password=:password order by id desc limit 1;"
   query_param={"mobile":mobile,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #token encode
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#my/profile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_object_update
from datetime import datetime
@app.get("/my/profile")
async def my_profile(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response={"status":1,"message":user}
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   await postgres_object_update(postgres_object,column_datatype,"background","users",[object])
   #final
   return response

#my/token refresh
from fastapi import Request
from fastapi.responses import JSONResponse
from function import jwt_token_encode
@app.get("/my/token-refresh")
async def my_token_refresh(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response=await jwt_token_encode(user,jwt_secret_key,30)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/delete-account
from fastapi import Request
from fastapi.responses import JSONResponse
@app.delete("/my/delete-account")
async def my_delete_account(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #check
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if user["is_protected"]==1:return {"status":1,"message":"protected user cant be deleted"}
   if user["type"] in ["admin"]:return {"status":1,"message":"type admin cant be deleted"}
   #logic
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":"account deleted"}
   #final
   return response

#my/message received
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from function import postgres_object_update
from datetime import datetime
@app.get("/my/message-received")
async def my_message_received(request:Request,background:BackgroundTasks,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by {order} limit {limit} offset {(page-1)*limit};"
   if mode=="unread":query=f"select * from message where parent_table='users' and parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background
   if output:
      object_list=[{"id":item["id"],"status":"read","updated_by_id":user["id"]} for item in output]
      response=await postgres_object_update(postgres_object,column_datatype,"background","message",object_list)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

#my/message inbox
from fastapi import Request
from fastapi.responses import JSONResponse
@app.get("/my/message-inbox")
async def my_message_inbox(request:Request,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
   if mode=="unread":query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/message thread
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from datetime import datetime
@app.get("/my/message-thread")
async def my_message_thread(request:Request,background:BackgroundTasks,user_id:int,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background
   query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"parent_id":user["id"]}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}

#my/message delete
from fastapi import Request
from fastapi.responses import JSONResponse
@app.delete("/my/message-delete")
async def my_message_delete(request:Request,mode:str,id:int=None):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   if mode=="created":
     query="delete from message where parent_table='users' and created_by_id=:created_by_id;"
     query_param={"created_by_id":user["id"]}
   if mode=="received":
     query="delete from message where parent_table='users' and parent_id=:parent_id;"
     query_param={"parent_id":user["id"]}
   if mode=="all":
     query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
     query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   if mode=="single":
     if not id:return JSONResponse(status_code=400,content={"status":0,"message":"id must"})
     query="delete from message where parent_table='users' and id=:id and (created_by_id=:created_by_id or parent_id=:parent_id);"
     query_param={"id":id,"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/parent read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_parent_read
@app.get("/my/parent-read")
async def my_parent_read(request:Request,table:str,parent_table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   response=await postgres_parent_read(postgres_object,table,parent_table,order,limit,(page-1)*limit,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/parent check
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_parent_check
@app.get("/my/parent-check")
async def my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   response=await postgres_parent_check(postgres_object,table,parent_table,parent_ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/update email
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
from function import postgres_object_update
@app.put("/my/update-email")
async def my_update_email(request:Request,email:str,otp:int):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #otp verify   
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   object={"id":user["id"],"updated_by_id":user["id"],"email":email}
   response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/update mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
from function import postgres_object_update
@app.put("/my/update-mobile")
async def my_update_mobile(request:Request,mobile:str,otp:int):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #otp verify
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   object={"id":user["id"],"updated_by_id":user["id"],"mobile":mobile}
   response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/location search
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_location_search
from function import where_clause
@app.get("/my/location-search")
async def my_location_search(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #where
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   response=await postgres_location_search(postgres_object,table,location,within,order,limit,(page-1)*limit,where_string,where_value)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/delete ids
from fastapi import Request
from fastapi.responses import JSONResponse
@app.delete("/my/delete-ids")
async def my_delete_ids(request:Request,table:str,ids:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #check      
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids.split(","))>3:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   #logic
   query=f"delete from {table} where created_by_id=:created_by_id and id in ({ids});"
   query_param={"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import where_clause
@app.get("/my/object-read")
async def my_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #where
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/object update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_object_update
from function import postgres_object_ownership_check
@app.put("/my/object-update")
async def my_object_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #check
   if table in ["spatial_ref_sys","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #object
   object=await request.json()
   object["updated_by_id"]=user["id"]
   response=await postgres_object_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   if table=="users":
      for item in ["email","mobile"]:
         if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   #logic
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/object delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import where_clause
@app.delete("/my/object-delete")
async def my_object_delete(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #check
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #where
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"delete from {table} {where_string};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#public/api-list
from fastapi import Request
@app.get("/public/api-list")
async def public_api_list(request:Request,mode:str=None):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  app=request.state.app
  #logic
  api_list=[route.path for route in app.routes]
  if mode=="admin":api_list=[route.path for route in app.routes if "/admin" in route.path]
  #final
  return {"status":1,"message":api_list}

#public/table-column
from fastapi import Request
@app.get("/public/table-column")
async def public_table_column(request:Request,table:str=None):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  #logic
  column_generic=["id","created_at","created_by_id","is_deleted","updated_at","updated_by_id","is_active","is_verified","is_protected"]
  schema_column=await postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
  if not table:
    output={}
    table_list=list(set([item['table_name'] for item in schema_column]))
    for table in table_list:
      output[table]={item["column_name"]:item["data_type"] for item in schema_column if item['table_name']==table and item["column_name"] not in column_generic}
  else:output={item["column_name"]:item["data_type"] for item in schema_column if item['table_name']==table and item["column_name"] not in column_generic}
  #final
  return {"status":1,"message":output}

#public/project meta
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from function import redis_key_builder
@app.get("/public/project-meta")
@cache(expire=60,key_builder=redis_key_builder)
async def public_project_meta(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   temp={k:await postgres_object.fetch_all(query=v,values={}) for k,v in query_dict.items()}
   response={"status":1,"message":temp}
   #final
   return response

#public/otp send mobile sns
from fastapi import Request
from fastapi.responses import JSONResponse
from config import sns_region_name,sns_access_key_id,sns_secret_access_key
import boto3,random
@app.get("/public/otp-send-mobile-sns")
async def public_otp_send_mobile_sns(request:Request,mobile:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   otp=random.randint(100000,999999)
   sns_client=boto3.client("sns",region_name=sns_region_name,aws_access_key_id=sns_access_key_id,aws_secret_access_key=sns_secret_access_key)
   output=sns_client.publish(PhoneNumber=mobile,Message=f"otp={otp}")
   #save otp
   query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;"
   query_param={"otp":otp,"mobile":mobile}
   await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#public/otp send email ses
from fastapi import Request
from fastapi.responses import JSONResponse
from config import ses_region_name,ses_access_key_id,ses_secret_access_key
import boto3,random
@app.get("/public/otp-send-email-ses")
async def public_otp_send_email_ses(request:Request,identity:str,email:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   otp=random.randint(100000,999999)
   ses_client=boto3.client("ses",region_name=ses_region_name,aws_access_key_id=ses_access_key_id,aws_secret_access_key=ses_secret_access_key)
   output=ses_client.send_email(Source=identity,Destination={"ToAddresses":[email]},Message={"Subject":{"Charset":"UTF-8","Data":"otp"},"Body":{"Text":{"Charset":"UTF-8","Data":str(otp)}}})
   #save otp
   query="insert into otp (otp,email) values (:otp,:email) returning *;"
   query_param={"otp":otp,"email":email}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"otp sent"}

#public/otp verify email
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
@app.get("/public/otp-verify-email")
async def public_otp_verify_email(request:Request,otp:int,email:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public/otp verify mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
@app.get("/public/otp-verify-mobile")
async def public_otp_verify_mobile(request:Request,otp:int,mobile:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public/object read
from fastapi import Request
from fastapi.responses import JSONResponse
from config import jwt_secret_key
from function import where_clause
from fastapi_cache.decorator import cache
from function import redis_key_builder
from function import postgres_add_creator_key
from function import postgres_add_action_count
@app.get("/public/object-read")
@cache(expire=60,key_builder=redis_key_builder)
async def public_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #check
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #whwere
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #creator key
   response=await postgres_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #action count
   response=await postgres_add_action_count(postgres_object,"likes",table,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   response=await postgres_add_action_count(postgres_object,"bookmark",table,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#private/object create
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_object_create
@app.post("/private/object-create")
async def private_object_create(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #check
   if table not in ["post","likes","bookmark","report","block","rating","comment","message","helpdesk"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #object
   object=await request.json()
   object["created_by_id"]=user["id"]
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   #logic
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#private/object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import where_clause
@app.get("/private/object-read")
async def private_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #where
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response

#private/s3 upload file
from fastapi import Request
from fastapi.responses import JSONResponse
from config import s3_access_key_id,s3_secret_access_key
from fastapi import UploadFile
import boto3,uuid
@app.post("/private/s3-upload-file")
async def private_s3_upload_file(request:Request,s3_region_name:str,s3_bucket_name:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   key=str(uuid.uuid4())+"-"+file.filename
   s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   s3_client.upload_fileobj(file.file,s3_bucket_name,key)
   s3_url=f"https://{s3_bucket_name}.s3.amazonaws.com/{key}"
   #final
   return {"status":1,"message":s3_url}

#private/s3 create presigned url
from fastapi import Request
from fastapi.responses import JSONResponse
from config import s3_access_key_id,s3_secret_access_key
import boto3,uuid
@app.get("/private/s3-create-presigned-url")
async def private_s3_create_presigned_url(request:Request,s3_region_name:str,s3_bucket_name:str,filename:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   if "." not in filename:return JSONResponse(status_code=400,content={"status":0,"message":"extension must"})
   key=str(uuid.uuid4())+"-"+filename
   s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=s3_bucket_name,Key=key,ExpiresIn=60,Conditions=[['content-length-range',1,250*1024]])
   output["s3_url"]=f"https://{s3_bucket_name}.s3.amazonaws.com/{key}"
   #final
   return {"status":1,"message":output}

#private/rekognition compare face
from fastapi import Request
from fastapi.responses import JSONResponse
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
import boto3
@app.get("/private/rekognition-compare-face")
async def private_rekognition_compare_face(request:Request,url_source:str,url_target:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   bucket_name_source=url_source.split("//",1)[1].split(".",1)[0]
   bucket_name_target=url_target.split("//",1)[1].split(".",1)[0]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.compare_faces(SourceImage={"S3Object":{"Bucket":bucket_name_source,"Name":url_source.rsplit("/",1)[1]}},TargetImage={"S3Object":{"Bucket":bucket_name_target,"Name":url_target.rsplit("/",1)[1]}},SimilarityThreshold=80)
   #final
   return {"status":1,"message":output}

#private/rekognition detetct label
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
@app.get("/private/rekognition-detect-label")
async def private_rekognition_detect_label(request:Request,url:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   bucket_name=url.split("//",1)[1].split(".",1)[0]
   key=url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MaxLabels=10,MinConfidence=90)
   #final
   return {"status":1,"message":output}

#private/rekognition detetct face
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
@app.get("/private/rekognition-detect-face")
async def private_rekognition_detect_face(request:Request,url:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   bucket_name=url.split("//",1)[1].split(".",1)[0]
   key=url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_faces(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},Attributes=['ALL'])
   #final
   return {"status":1,"message":output}

#private/rekognition detect moderation
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
@app.get("/private/rekognition-detect-moderation")
async def private_rekognition_detect_moderation(request:Request,url:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   bucket_name=url.split("//",1)[1].split(".",1)[0]
   key=url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_moderation_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MinConfidence=80)
   #final
   return {"status":1,"message":output}

#private/openai
from fastapi import Request
from fastapi.responses import JSONResponse
from config import openai_secret_key
from langchain_community.llms import OpenAI
@app.get("/private/openai")
async def private_openai(request:Request,text:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   llm=OpenAI(api_key=openai_secret_key,temperature=0.7)
   output=llm(text)
   #final
   return {"status":1,"message":output}

#admin/postgres clean
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_clean
@app.delete("/admin/postgres-clean")
async def admin_pclean(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   response=await postgres_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin/csv create
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_create
@app.post("/admin/csv-create")
async def admin_csv_create(request:Request,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #csv to object
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin/csv update
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_update
@app.put("/admin/csv-update")
async def admin_csv_update(request:Request,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #csv to object
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin/s3 delete url
from fastapi import Request
from fastapi.responses import JSONResponse
from config import s3_access_key_id,s3_secret_access_key
import boto3
@app.delete("/admin/s3-delete-url")
async def admin_s3_delete_url(request:Request,s3_region_name:str,s3_bucket_name:str,url:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   key=url.rsplit("/",1)[1]
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Object(s3_bucket_name,key).delete()
   #final
   return {"status":1,"message":output}

#admin/s3 delete all
from fastapi import Request
from fastapi.responses import JSONResponse
from config import s3_access_key_id,s3_secret_access_key
import boto3
@app.delete("/admin/s3-delete-all")
async def admin_s3_delete_all(request:Request,s3_bucket_name:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Bucket(s3_bucket_name).objects.all().delete()
   #final
   return {"status":1,"message":output}

#admin/object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import where_clause
@app.get("/admin/object-read")
async def admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #where
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response

#admin/object update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_object_update
@app.put("/admin/object-update")
async def admin_object_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   column_datatype=request.state.column_datatype
   #check
   if table in ["spatial_ref_sys","otp","log"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #object
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["updated_by_id"]=user["id"]
   #logic
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin/delete ids
from fastapi import Request
from fastapi.responses import JSONResponse
@app.put("/admin/delete-ids")
async def admin_delete_ids(request:Request,table:str,ids:str):
   #middleware
   postgres_object=request.state.postgres_object
   user=request.state.user
   #logic
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#admin/postgres-qrunner
from fastapi import Request
from fastapi.responses import JSONResponse
@app.get("/admin/postgres-qrunner")
async def admin_postgres_qrunner(request:Request,query:str):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  #logic
  for item in ["insert","update","delete","alter","drop"]:
    if item in query:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed in query"})
  output=await postgres_object.fetch_all(query=query,values={})
  #final
  return {"status":1,"message":output}

#admin/update-api-access
from fastapi import Request
from pydantic import BaseModel
class schema_update_api_access(BaseModel):
  user_id:int
  api_access:str|None=None
@app.put("/admin/update-api-access")
async def admin_update_api_access(request:Request,body:schema_update_api_access):
  #middleware
  postgres_object=request.state.postgres_object
  user=request.state.user
  app=request.state.app
  #logic
  api_admin_list=[route.path for route in app.routes if "/admin" in route.path]
  api_admin_str=",".join(api_admin_list)
  if body.api_access:
    for item in body.api_access.split(","):
      if item not in api_admin_str:return JSONResponse(status_code=400,content={"status":0,"message":"wrong api access string"})
  query="update users set api_access=:api_access where id=:id returning *"
  query_param={"id":body.user_id,"api_access":body.api_access}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  #final
  return {"status":1,"message":output}


#postgres location search
async def postgres_location_search(postgres_object,table,location,within,order,limit,offset,where_string,where_value):
  long,lat=float(location.split(",")[0]),float(location.split(",")[1])
  min_meter,max_meter=int(within.split(",")[0]),int(within.split(",")[1])
  query=f'''
  with
  x as (select * from {table} {where_string}),
  y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x)
  select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {offset};
  '''
  query_param=where_value
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#where clause
import hashlib
from datetime import datetime
async def where_clause(param,column_datatype):
  param={k:v for k,v in param.items() if k in column_datatype}
  param={k:v for k,v in param.items() if k not in ["location","metadata"]}
  where_key_value={k:v.split(',',1)[1] for k,v in param.items()}
  where_key_operator={k:v.split(',',1)[0] for k,v in param.items()}
  key_list=[f"({k} {where_key_operator[k]} :{k} or :{k} is null)" for k,v in where_key_value.items()]
  key_joined=' and '.join(key_list)
  where_string=f"where {key_joined}" if key_joined else ""
  for k,v in where_key_value.items():
    if k in column_datatype:datatype=column_datatype[k]
    else:return {"status":0,"message":f"{k} column not in column_datatype"}
    if k in ["password","google_id"]:where_key_value[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
    if "int" in datatype:where_key_value[k]=int(v) if v else None
    if datatype in ["numeric"]:where_key_value[k]=round(float(v),3) if v else None
    if "time" in datatype:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if datatype in ["date"]:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if datatype in ["ARRAY"]:where_key_value[k]=v.split(",") if v else None
  return {"status":1,"message":[where_string,where_key_value]}
  

  
#postgres object update
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_update(postgres_object,column_datatype,mode,table,object_list):
  if not object_list:return {"status":0,"message":"object list empty"}
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      if k in column_datatype:datatype=column_datatype[k]
      else:return {"status":0,"message":f"{k} column not in column_datatype"}
      if not v:query_param_list[index][k]=None
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if "time" in datatype:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
  background=BackgroundTasks()
  output=None
  if len(object_list)==1:
    if mode=="normal":output=await postgres_object.fetch_all(query=query,values=query_param_list[0])
    if mode=="background":background.add_task(await postgres_object.fetch_all(query=query,values=query_param_list[0]))
  else:
    if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
    if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
  return {"status":1,"message":output}

#postgres parent read
async def postgres_parent_read(postgres_object,table,parent_table,order,limit,offset,created_by_id):
  query=f"select parent_id from {table} where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null) order by {order} limit {limit} offset {offset};"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_list=[item["parent_id"] for item in output]
  query=f"select * from {parent_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#postgres parent check
async def postgres_parent_check(postgres_object,table,parent_table,parent_ids,created_by_id):
  parent_ids_list=[int(item) for item in parent_ids.split(",")]
  query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null);"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_filtered=list(set([item["parent_id"] for item in output if item["parent_id"]]))
  return {"status":1,"message":parent_ids_filtered}

#postgres object ownership check
async def postgres_object_ownership_check(postgres_object,table,id,user_id):
  if table=="users":
    if id!=user_id:return {"status":0,"message":"ownership issue"}
  if table!="users":
    query=f"select * from {table} where id=:id;"
    query_param={"id":id}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    object=output[0] if output else None
    if not object:return {"status":0,"message":"no object"}
    if object["created_by_id"]!=user_id:return {"status":0,"message":"object ownership issue"}
  return {"status":1,"message":"done"}

#postgres clean
async def postgres_clean(postgres_object):
  for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
    query=f"delete from {table} where created_by_id not in (select id from users);"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  for table in ["likes","bookmark","report","block","rating","comment","message"]:
    for parent_table in ["users","post","comment"]:
      query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}

#csv to object list
import csv,codecs
async def csv_to_object_list(file):
  if file.content_type!="text/csv":return {"status":0,"message":"file extension must be csv"}
  file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
  object_list=[]
  for row in file_csv:
    object_list.append(row)
  await file.close()
  return {"status":1,"message":object_list}


#postgres otp verify
from datetime import datetime,timezone
async def postgtes_otp_verify(postgres_object,otp,email,mobile):
  if not otp:return {"status":0,"message":"otp mandatory"}
  if email and mobile:return {"status":0,"message":"only one contact allowed"}
  if not email and not mobile:return {"status":0,"message":"both contact cant be null"}
  if email:
    query="select * from otp where email=:email order by id desc limit 1;"
    query_param={"email":email}
  if mobile:
    query="select * from otp where mobile=:mobile order by id desc limit 1;"
    query_param={"mobile":mobile}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if not output:return {"status":0,"message":"otp not found"}
  if int(datetime.now(timezone.utc).strftime('%s'))-int(output[0]["created_at"].strftime('%s'))>6000000000000:return {"status":0,"message":"otp expired"}
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
  return {"status":1,"message":"otp verifed"}

#postgres add action count
async def postgres_add_action_count(postgres_object,action,object_table,object_list):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action}_count"
  object_list=[dict(item)|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}

#postgres add creator key
async def postgres_add_creator_key(postgres_object,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[dict(item)|{"created_by_username":None} for item in object_list]
  user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
  if user_ids:
    query=f"select * from users where id in ({user_ids});"
    query_param={}
    object_user_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_user_list:
         if x["created_by_id"]==y["id"]:
           x["created_by_username"]=y["username"]
           break
  return {"status":1,"message":object_list}




#jwt token encode
import jwt,json,time
from datetime import datetime,timedelta
async def jwt_token_encode(user,jwt_secret_key,expiry_days):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"],"is_protected":user["is_protected"]}
  data=json.dumps(data,default=str)
  expiry_time=time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,jwt_secret_key)
  return {"status":1,"message":token}

#redis key builder
from fastapi import Request,Response
def redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
  param=":".join(param)
  return param










