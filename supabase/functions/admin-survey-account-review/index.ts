// Urbanfold admin account deletion REVIEW ONLY. No mutation or deletion endpoint.
// Access must be checked on the server. Never embed service-role secrets in a webpage.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const URL = Deno.env.get("SUPABASE_URL")!;
const ANON = Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ADMIN_UID = "8d3f6f84-8af9-4ad8-82e7-53db9850d6db";
const origins = new Set(["https://urbanfold.github.io"]);
const buckets = ["exterior-photos", "sketch-photos", "room-photos"];
const json = (body: unknown, status = 200, origin = "") => new Response(JSON.stringify(body), {
  status, headers: {"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store",
  "Access-Control-Allow-Origin":origin,"Access-Control-Allow-Headers":"authorization, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS","Vary":"Origin"}
});
Deno.serve(async (req) => {
  const origin = req.headers.get("origin") || "";
  if (!origins.has(origin)) return json({error:"Origin not allowed"},403);
  if (req.method === "OPTIONS") return json({},200,origin);
  if (req.method !== "POST") return json({error:"Method not allowed"},405,origin);
  const bearer = /^Bearer (.+)$/.exec(req.headers.get("authorization") || "");
  if (!bearer) return json({error:"Sign in required"},401,origin);
  const auth = createClient(URL, ANON, { auth: { persistSession:false, autoRefreshToken:false } });
  const { data: { user }, error: authError } = await auth.auth.getUser(bearer[1]);
  if (authError || !user || user.id !== ADMIN_UID || !user.email_confirmed_at)
    return json({error:"Administrator access required"},403,origin);
  let email = "";
  try { email = String((await req.json()).email || "").trim().toLowerCase(); } catch { return json({error:"Invalid request"},400,origin); }
  if (email.length > 254 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({error:"Enter a valid account email"},400,origin);
  const db = createClient(URL, SERVICE, { auth: {persistSession:false,autoRefreshToken:false} });
  // Auth admin list is paginated; never assume the requested user appears on the first page.
  let matching: {id:string;email?:string} | undefined;
  for (let page=1;page<=100;page++) {
    const {data,error} = await db.auth.admin.listUsers({page,perPage:100});
    if (error) return json({error:"Account lookup unavailable"},500,origin);
    matching = data.users.find(u=>u.email?.toLowerCase()===email);
    if (matching || data.users.length<100) break;
  }
  if (!matching) return json({found:false},200,origin);
  if (matching.id===ADMIN_UID) return json({error:"Administrator account cannot be reviewed here"},403,origin);
  const {data:properties,error:pError} = await db.from("properties").select("id,address,postcode,created_at").eq("user_id", matching.id);
  if (pError) return json({error:"Property lookup unavailable"},500,origin);
  const surveyRows = [];
  for (const property of properties || []) {
    const pid=property.id;
    const count = async (table:string,column:string,value:string) => {
      const {count,error}=await db.from(table).select("*",{count:"exact",head:true}).eq(column,value);
      if(error) throw new Error("Count failed for "+table);
      return count || 0;
    };
    const {data:rooms,error:rError}=await db.from("rooms").select("id").eq("property_id",pid);
    if(rError) return json({error:"Room lookup unavailable"},500,origin);
    let roomPhotoReferences=0;
    for (const room of rooms||[]) roomPhotoReferences+=await count("room_photos","room_id",room.id);
    const storage:Record<string,number>={};
    for(const bucket of buckets) {
      const {data:objects,error:oError}=await db.storage.from(bucket).list(pid,{limit:1000});
      if(oError) return json({error:"Storage lookup unavailable"},500,origin);
      storage[bucket]=(objects||[]).filter(o=>o.id).length;
    }
    surveyRows.push({...property, rooms:rooms?.length||0, photoReferences:{
      exterior:await count("exterior_photos","property_id",pid),
      extensions:await count("extension_photos","property_id",pid),
      sketches:await count("sketch_photos","property_id",pid),
      rooms:roomPhotoReferences
    },storageFiles:storage});
  }
  const {data:purchases,error:payError}=await db.from("survey_credit_purchases").select("live_mode").eq("user_id",matching.id);
  if(payError) return json({error:"Payment lookup unavailable"},500,origin);
  const {count:profileRows,error:profileError}=await db.from("users").select("*",{count:"exact",head:true}).eq("id",matching.id);
  if(profileError) return json({error:"Profile lookup unavailable"},500,origin);
  return json({found:true,account:{email:matching.email,accountId:matching.id},surveys:surveyRows,
    paymentRecords:purchases?.length||0,paymentBreakdown:{sandbox:(purchases||[]).filter(p=>p.live_mode===false).length,live:(purchases||[]).filter(p=>p.live_mode===true).length},
    profileRows:profileRows||0,warning:"Review only. Payment/financial records may require separate retention. No data has been deleted."},200,origin);
});
