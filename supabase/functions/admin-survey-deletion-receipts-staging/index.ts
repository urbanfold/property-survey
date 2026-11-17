// Staging-only completed-deletion receipt lookup. Read-only, admin-authorized.
// No outbound mail: stage delivery must use capture rather than customer email.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const BASE=Deno.env.get("SUPABASE_URL")!;
const ANON=Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ADMIN="b83f87d8-abf2-4800-beab-8279917804c7";
const ORIGIN="https://urbanfold.github.io";
const send=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Headers":"authorization, apikey, content-type","Access-Control-Allow-Methods":"POST, OPTIONS","Vary":"Origin"}});
Deno.serve(async req=>{
 if(req.headers.get("origin")!==ORIGIN)return send({error:"Origin forbidden"},403);
 if(req.method==="OPTIONS")return send({});
 if(req.method!=="POST")return send({error:"POST required"},405);
 const token=/^Bearer (.+)$/.exec(req.headers.get("authorization")||"")?.[1];
 if(!token)return send({error:"Sign in required"},401);
 const auth=createClient(BASE,ANON,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:{user},error}=await auth.auth.getUser(token);
 if(error||!user||user.id!==ADMIN||!user.email_confirmed_at)return send({error:"Admin permission required"},403);
 let query:any;
 try{query=await req.json();}catch{return send({error:"Invalid JSON"},400);}
 const email=String(query.email||"").trim().toLowerCase();
 if(!email.endsWith("@example.invalid")||email.length>254)return send({error:"Staging dummy accounts only"},403);
 const db=createClient(BASE,SERVICE,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data,error:dbError}=await db.from("staging_account_deletion_audit")
  .select("id,target_email,status,property_count,removed_storage_files,created_at,completed_at")
  .eq("target_email",email).eq("status","completed").order("completed_at",{ascending:false}).limit(10);
 if(dbError)return send({error:"Receipt records unavailable"},503);
 return send({receipts:data||[],notes:"Read only. Draft emails are not sent automatically. Never send to @example.invalid addresses."});
});
