// STAGING-ONLY dummy-account deletion test. Never deploy this function to live.
// Administrator authorization is enforced server-side using a fixed verified staging Auth UID.
// Two stages: prepare (records a short-lived pending request) and execute (requires exact email).
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const BASE = Deno.env.get("SUPABASE_URL")!;
const ANON = Deno.env.get("SUPABASE_ANON_KEY")!;
const SECRET = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ADMIN = "b83f87d8-abf2-4800-beab-8279917804c7";
const ORIGIN = "https://urbanfold.github.io";
const BUCKETS = ["exterior-photos","extension-photos","sketch-photos","room-photos"];
const reply = (result:unknown, status=200) => new Response(JSON.stringify(result),{status,headers:{"Content-Type":"application/json","Cache-Control":"no-store","Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Headers":"authorization,apikey,content-type","Access-Control-Allow-Methods":"POST,OPTIONS","Vary":"Origin"}});
const client = () => createClient(BASE,SECRET,{auth:{persistSession:false,autoRefreshToken:false}});
async function insistOk<T>(res:{data:T,error:any},context:string):Promise<T> {if(res.error)throw Error(context+": "+res.error.message);return res.data;}
Deno.serve(async request=>{
 if(request.headers.get("origin")!==ORIGIN)return reply({error:"Origin not allowed"},403);
 if(request.method==="OPTIONS")return reply({},200);
 if(request.method!=="POST")return reply({error:"POST only"},405);
 const jwt=/^Bearer (.+)$/.exec(request.headers.get("authorization")||"")?.[1];
 if(!jwt)return reply({error:"Sign in required"},401);
 const auth=createClient(BASE,ANON,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:{user},error}=await auth.auth.getUser(jwt);
 if(error||!user||user.id!==ADMIN||!user.email_confirmed_at)return reply({error:"Not authorized"},403);
 let payload:any;
 try{payload=await request.json();}catch{return reply({error:"Invalid JSON"},400);}
 const email=String(payload.email||"").trim().toLowerCase();
 // Limit this test tool to reserved non-deliverable test addresses only.
 if(!email.endsWith("@example.invalid")||email.length>254)return reply({error:"Staging dummy accounts only"},403);
 const db=client();
 try{
  const candidates=await db.auth.admin.listUsers({page:1,perPage:100});
  const users=await insistOk(candidates,"List Auth accounts");
  if(users.users.length===100)throw Error("User list exceeds safe preview limit");
  const target=users.users.find(u=>u.email?.toLowerCase()===email);
  if(!target||target.id===ADMIN)return reply({error:"Target account not found or protected"},404);
  const properties=await insistOk(await db.from("properties").select("id,address").eq("user_id",target.id),"Read owned properties");
  const {count:payments,error:pErr}=await db.from("survey_credit_purchases").select("*",{count:"exact",head:true}).eq("user_id",target.id);
  if(pErr)throw pErr;
  if(payments!==0)return reply({error:"Payment records exist. Manual retention review required."},409);
  if(payload.action==="prepare"){
   const {data:row,error:insertError}=await db.from("staging_account_deletion_audit").insert({
    target_user_id:target.id,target_email:email,status:"pending",prepared_by:ADMIN,
    property_count:properties.length
   }).select("id,created_at").single();
   if(insertError)throw insertError;
   return reply({prepared:true,requestId:row.id,expiresInMinutes:15,
      email,propertyCount:properties.length,addresses:properties.map(p=>p.address),
      warning:"Staging dummy only. Irreversible after confirmed. Enter exact email to execute."});
  }
  if(payload.action!=="execute")return reply({error:"Unknown action"},400);
  if(String(payload.confirmEmail||"").trim().toLowerCase()!==email)return reply({error:"Type the exact registered email to confirm"},400);
  if(payload.acknowledged!==true)return reply({error:"Explicit confirmation is required"},400);
  const requestId=String(payload.requestId||"");
  if(!/^[0-9a-f-]{36}$/i.test(requestId))return reply({error:"Invalid request ID"},400);
  const expiry=new Date(Date.now()-15*60*1000).toISOString();
  const {data:claim,error:claimError}=await db.from("staging_account_deletion_audit").update({status:"processing",started_at:new Date().toISOString()})
   .eq("id",requestId).eq("target_user_id",target.id).eq("target_email",email).eq("prepared_by",ADMIN)
   .eq("status","pending").gte("created_at",expiry).select("id,property_count").maybeSingle();
  if(claimError)throw claimError;
  if(!claim)return reply({error:"Confirmation expired, already used or does not match account"},409);
  if(claim.property_count!==properties.length)throw Error("Survey count changed. Stop and review.");
  let removedFiles=0;
  for(const property of properties){
   for(const bucket of BUCKETS){
     // List the complete property prefix; reject pages that might hide additional files.
     const files=await insistOk(await db.storage.from(bucket).list(property.id,{limit:1000}),"List storage "+bucket);
     if(files.length>=1000)throw Error("Storage listing too large; manual investigation needed");
     const paths=files.filter(x=>x.id).map(x=>property.id+"/"+x.name);
     if(paths.length){
       const deleted=await db.storage.from(bucket).remove(paths);
       if(deleted.error)throw Error("Delete storage "+bucket+": "+deleted.error.message);
       if((deleted.data||[]).length!==paths.length)throw Error("Storage removal returned incomplete result");
       removedFiles+=paths.length;
     }
   }
   const rooms=await insistOk(await db.from("rooms").select("id").eq("property_id",property.id),"Read rooms");
   for(const room of rooms)await insistOk(await db.from("room_photos").delete().eq("room_id",room.id),"Delete room photo refs");
   await insistOk(await db.from("rooms").delete().eq("property_id",property.id),"Delete rooms");
   for(const table of ["exterior_photos","extension_photos","sketch_photos","extensions"])
     await insistOk(await db.from(table).delete().eq("property_id",property.id),"Delete "+table);
   await insistOk(await db.from("properties").delete().eq("id",property.id).eq("user_id",target.id),"Delete property");
  }
  // No Stripe/payment history can be present: checked before prepare AND execute.
  await insistOk(await db.from("survey_free_allocations").delete().eq("user_id",target.id),"Delete free allocations");
  const deletedAuth=await db.auth.admin.deleteUser(target.id);
  if(deletedAuth.error)throw Error("Delete Auth user: "+deletedAuth.error.message);
  await insistOk(await db.from("staging_account_deletion_audit").update({status:"completed",completed_at:new Date().toISOString(),removed_storage_files:removedFiles}).eq("id",requestId),"Finish audit");
  return reply({completed:true,email,propertyCount:properties.length,removedStorageFiles:removedFiles,
    message:"Staging dummy deletion completed. No confirmation email was sent automatically."});
 }catch(e){
   // A partial failure needs manual investigation. Do not report success or auto-retry.
   return reply({error:"Deletion stopped: "+String((e as Error).message||e)+". Check audit and remaining records before retry."},500);
 }
});
