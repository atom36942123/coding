#docker
#image pull=docker pull postgres
#container run=docker run --name postgres_container_1 -e POSTGRES_PASSWORD=password -d -p 5432:5432  postgres
#container login=docker exec -it 09897e9d1267 bash
#psql login=psql -U postgres
#host=docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres_container_1
#url="postgres://postgres:password@172.17.0.3:5432/postgres?sslmode=disable"


#run=python postgress.py
url="postgresql://localhost:5432/postgres"

import asyncpg
import datetime
async def main():
   conn = await asyncpg.connect(url)
   await conn.execute('''CREATE TABLE if not exists users(id serial PRIMARY KEY,username text,dob date)''')
   await conn.execute('''INSERT INTO users(username, dob) VALUES($1, $2)''', 'atom',datetime.date(1984, 3, 1))
   row = await conn.fetchrow('SELECT * FROM users WHERE username = $1', 'atom')
   print(row)
   await conn.close()
  
import asyncio  
if __name__ == "__main__":
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(main())

#reset
# drop schema public cascade;
# create schema public;
# DO
# $$ DECLARE r RECORD; BEGIN FOR r IN
# (SELECT tablename FROM pg_tables WHERE schemaname=current_schema() and tablename not in ('spatial_ref_sys')) LOOP
# EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || '
# CASCADE'; END LOOP;
# END $$;

#schema
# extension=select * from pg_extension;
# database=select *,pg_size_pretty(pg_database_size(datname)) as db_size from pg_database;
# namespace=select * from pg_namespace;
# routine=select * from pg_proc where proname='function_set_updated_at_now'
# trigger=select * from information_schema.triggers;
# activity=select * from pg_stat_activity;
# constraint=select * from information_schema.constraint_column_usage where constraint_schema='public';
# index=select * from pg_indexes where schemaname='public';
# rules=select * from pg_rules;
# identity=select * from pg_attribute where attnum>0 and attidentity in ('a','d');
# table=select * from information_schema.tables where table_schema='public' and table_type='BASE TABLE';
# column=select * from information_schema.columns where table_schema='public';
# table master=with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),y as (select table_name,count(*) as count_column from information_schema.columns group by table_name) select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;
# column master=select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by column_name order by count desc;

#drop
# drop connection=SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname='test' AND pid <> pg_backend_pid();
# drop constraint all=SELECT 'ALTER TABLE '||table_name||' DROP CONSTRAINT '||constraint_name||';' FROM information_schema.constraint_table_usage where constraint_schema='public';
# drop view all=SELECT 'DROP VIEW ' || table_name || ';' FROM information_schema.views WHERE table_schema NOT IN ('pg_catalog', 'information_schema') AND table_name !~ '^pg_';
# drop triggers all=SELECT 'DROP TRIGGER ' || trigger_name || ' ON ' || event_object_table || ';' FROM information_schema.triggers WHERE trigger_schema = 'public';
# drop index all=select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;

#exim
# export=\copy post to 'filepath' with (format csv,header);
# export column=\copy (query) to 'filepath' with (format csv,header);
# export database from terminal=pg_dump atom > /Users/atom/Downloads/atom_backup.sql
# import=\copy post from 'filepath' with (format csv,header);
# import column=\copy post(type,title,description,link,tag) from 'filepath' with (format csv,header);
# import database from terminal=psql atom < /Users/atom/Downloads/atom_backup.sql

#crud
# tag read one=select * from post where 'investor'=any(tag);
# tag read all=select * from post where tag @> '{"xxx","yyy"}';
# tag read any=select * from post where tag && '{"xxx","yyy"}';
# tag read regex=select * from post where (array_to_string(tag,'')~*'xx');
# tag replace=update post set tag=array_replace(tag,'xxx','yyy')
# tag append=update box set tag=array_append(tag,'xxx') where id=1;
# tag append no duplicate=update box set tag=(select array_agg(distinct t) from unnest(tag||'{xxx}') as t) where id=1;
# tag delete=update box set tag=array_remove(tag,'atom') where id=1;

#follow-following
# with 
# x as (select * from follow where created_by_id in (select user_id from follow where created_by_id=1)),
# y as (select distinct(created_by_id) from x where user_id=1 limit 10 offset 0)
# select u.* from y left join users as u on y.created_by_id=u.id
 
#follow-following not back
# with 
# x as (select * from follow where created_by_id in (select user_id from follow where created_by_id=1)),
# y as (select distinct(created_by_id) from x where created_by_id not in (select created_by_id from x where user_id=1) limit 10 offset 0)
# select * from y left join users as u on y.created_by_id=u.id

#follow-following not back from login user perspective
# with 
# x as (select created_by_id from follow where user_id=2 and created_by_id not in (select user_id from follow where created_by_id=2) limit 10 offset 0)
# select * from x left join users as u on x.created_by_id=u.id