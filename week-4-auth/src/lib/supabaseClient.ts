import {createClient} from '@supabase/supabase-js'
import 'dotenv/config'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY

if(!supabaseKey || !supabaseUrl){
    throw new Error("Missing SUPABASE_KEY or SUPABASE_Url")
}

export const supabase = createClient(supabaseUrl,supabaseKey) 